"""Pydantic schemas for the "Найти дешевле" feature."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.db.models.cheaper import CheaperStatus


class CheaperSearchRequest(BaseModel):
    url: HttpUrl = Field(..., description="Product URL from any marketplace")


class CheaperSearchCreated(BaseModel):
    task_id: str
    status: CheaperStatus


class Offer(BaseModel):
    domain: str
    price: float
    product_name: str | None = None
    product_url: str | None = None
    img_url: str | None = None
    rating: float | None = None
    review_cnt: int | None = None


class PlannedShop(BaseModel):
    domain: str


class CheaperSearchResult(BaseModel):
    task_id: str
    status: CheaperStatus
    url: str
    orig_domain: str | None = None
    product_name: str | None = None
    product_img_url: str | None = None
    orig_price: float | None = None
    currency: str | None = "RUR"
    planned_shops: list[PlannedShop] | None = None
    offers: list[Offer] | None = None
    error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class CheaperEvent(BaseModel):
    """Live event pushed via WS / Redis pubsub."""

    type: str  # 'planned_shops' | 'offer' | 'progress' | 'done' | 'error'
    task_id: str
    data: dict | None = None
