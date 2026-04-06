"""Authentication endpoints: register, login, profile."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, DbSession
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User


router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schemas ───────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    subscription_plan: str
    subscription_expires_at: datetime | None
    has_active_subscription: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


# ── Endpoints ─────────────────────────────────────────────────────


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: DbSession):
    """Register a new user account."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        is_active=True,
        is_verified=True,
        subscription_plan="free",
    )
    db.add(user)
    await db.flush()

    return _make_tokens(user.id)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: DbSession):
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if (
        not user
        or not user.hashed_password
        or not verify_password(data.password, user.hashed_password)
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    user.update_last_login()
    return _make_tokens(user.id)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: DbSession):
    """Refresh access token."""
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    return _make_tokens(user.id)


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser):
    """Get current user profile."""
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        subscription_plan=user.subscription_plan,
        subscription_expires_at=user.subscription_expires_at,
        has_active_subscription=user.has_active_subscription,
        created_at=user.created_at,
    )


@router.post("/change-password")
async def change_password(data: ChangePasswordRequest, user: CurrentUser, db: DbSession):
    """Change password for current user."""
    if not user.hashed_password or not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Wrong current password")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user.hashed_password = hash_password(data.new_password)
    return {"ok": True}


# ── Helpers ───────────────────────────────────────────────────────


def _make_tokens(user_id: int) -> TokenResponse:
    from app.config import settings

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
