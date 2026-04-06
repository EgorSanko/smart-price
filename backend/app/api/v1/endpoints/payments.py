"""Payment endpoints: create payment, webhook, subscription status."""

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, DbSession
from app.config import settings
from app.db.models.payment import Payment
from app.db.models.user import User


logger = structlog.get_logger()

router = APIRouter(prefix="/payments", tags=["payments"])


# ── Plan config ───────────────────────────────────────────────────

PLANS = {
    "pro": {"name": "Pro", "price": 299.00, "days": 30},
    "business": {"name": "Business", "price": 799.00, "days": 30},
}


# ── Schemas ───────────────────────────────────────────────────────


class CreatePaymentRequest(BaseModel):
    plan: str  # "pro" or "business"


class CreatePaymentResponse(BaseModel):
    confirmation_url: str
    payment_id: str


class SubscriptionInfo(BaseModel):
    plan: str
    plan_name: str
    is_active: bool
    expires_at: datetime | None
    days_remaining: int | None


class PaymentHistoryItem(BaseModel):
    id: int
    amount: float
    plan: str
    status: str
    created_at: datetime
    confirmed_at: datetime | None

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────


@router.post("/create", response_model=CreatePaymentResponse)
async def create_payment(data: CreatePaymentRequest, user: CurrentUser, db: DbSession):
    """Create a YooKassa payment for subscription."""
    plan_info = PLANS.get(data.plan)
    if not plan_info:
        raise HTTPException(status_code=400, detail="Invalid plan. Use 'pro' or 'business'")

    description = f"Smart Price — подписка {plan_info['name']} на {plan_info['days']} дней"

    # Try YooKassa SDK
    try:
        from yookassa import Configuration
        from yookassa import Payment as YKPayment

        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

        idempotency_key = str(uuid.uuid4())
        yk_payment = YKPayment.create(
            {
                "amount": {"value": f"{plan_info['price']:.2f}", "currency": "RUB"},
                "confirmation": {"type": "redirect", "return_url": settings.YOOKASSA_RETURN_URL},
                "capture": True,
                "description": description,
                "metadata": {"user_id": str(user.id), "plan": data.plan, "email": user.email},
            },
            idempotency_key,
        )

        payment_id = yk_payment.id
        confirmation_url = yk_payment.confirmation.confirmation_url

    except ImportError:
        # YooKassa SDK not installed — use mock for development
        payment_id = f"mock-{uuid.uuid4().hex[:12]}"
        confirmation_url = f"{settings.YOOKASSA_RETURN_URL}?mock=1&payment_id={payment_id}"
        logger.warning("yookassa_sdk_not_installed_using_mock")
    except Exception as e:
        # YooKassa credentials not configured — mock
        if not settings.YOOKASSA_SHOP_ID:
            payment_id = f"mock-{uuid.uuid4().hex[:12]}"
            confirmation_url = f"{settings.YOOKASSA_RETURN_URL}?mock=1&payment_id={payment_id}"
            logger.warning("yookassa_not_configured_using_mock")
        else:
            logger.error("yookassa_create_failed", error=str(e))
            raise HTTPException(status_code=502, detail="Payment service error")

    # Save payment record
    payment = Payment(
        user_id=user.id,
        yookassa_payment_id=payment_id,
        amount=plan_info["price"],
        plan=data.plan,
        status="pending",
        description=description,
    )
    db.add(payment)
    await db.flush()

    logger.info("payment_created", user_id=user.id, plan=data.plan, payment_id=payment_id)

    return CreatePaymentResponse(
        confirmation_url=confirmation_url,
        payment_id=payment_id,
    )


@router.post("/webhook")
async def payment_webhook(request: Request, db: DbSession):
    """Handle YooKassa payment notifications."""
    body = await request.json()

    event_type = body.get("event")
    payment_obj = body.get("object", {})
    yk_payment_id = payment_obj.get("id")

    logger.info("yookassa_webhook", event=event_type, payment_id=yk_payment_id)

    if not yk_payment_id:
        return {"ok": True}

    # Find our payment record
    result = await db.execute(select(Payment).where(Payment.yookassa_payment_id == yk_payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        logger.warning("webhook_payment_not_found", payment_id=yk_payment_id)
        return {"ok": True}

    if event_type == "payment.succeeded":
        payment.status = "succeeded"
        payment.confirmed_at = datetime.now(UTC)

        # Activate subscription
        user_result = await db.execute(select(User).where(User.id == payment.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            plan_info = PLANS.get(payment.plan, PLANS["pro"])
            user.subscription_plan = payment.plan
            user.subscription_expires_at = datetime.now(UTC) + timedelta(days=plan_info["days"])
            logger.info("subscription_activated", user_id=user.id, plan=payment.plan)

    elif event_type == "payment.canceled":
        payment.status = "canceled"

    return {"ok": True}


@router.post("/mock-confirm/{payment_id}")
async def mock_confirm_payment(payment_id: str, db: DbSession):
    """Mock payment confirmation for testing without YooKassa credentials."""
    result = await db.execute(select(Payment).where(Payment.yookassa_payment_id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == "succeeded":
        return {"ok": True, "message": "Already confirmed"}

    payment.status = "succeeded"
    payment.confirmed_at = datetime.now(UTC)

    user_result = await db.execute(select(User).where(User.id == payment.user_id))
    user = user_result.scalar_one_or_none()
    if user:
        plan_info = PLANS.get(payment.plan, PLANS["pro"])
        user.subscription_plan = payment.plan
        user.subscription_expires_at = datetime.now(UTC) + timedelta(days=plan_info["days"])

    return {"ok": True, "message": "Payment confirmed, subscription activated"}


@router.get("/subscription", response_model=SubscriptionInfo)
async def get_subscription(user: CurrentUser):
    """Get current subscription status."""
    days_remaining = None
    is_active = user.has_active_subscription

    if user.subscription_expires_at and is_active:
        delta = user.subscription_expires_at - datetime.now(UTC)
        days_remaining = max(0, delta.days)

    plan_names = {"free": "Бесплатный", "pro": "Pro", "business": "Business"}

    return SubscriptionInfo(
        plan=user.subscription_plan,
        plan_name=plan_names.get(user.subscription_plan, user.subscription_plan),
        is_active=is_active,
        expires_at=user.subscription_expires_at,
        days_remaining=days_remaining,
    )


@router.get("/history", response_model=list[PaymentHistoryItem])
async def get_payment_history(user: CurrentUser, db: DbSession):
    """Get user's payment history."""
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()
