from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PriceStats(BaseModel):
    min: float
    median: float
    mean: float
    max: float
    stdev: float
    count: int
    currency: str


class OfferLite(BaseModel):
    title: str
    price_num: float
    currency: str
    shop: str | None = None
    marketplace: str
    url: str
    image: str | None = None


class RedFlag(BaseModel):
    severity: Literal["info", "warn", "danger"]
    text: str


class AnalyzeAlternatives(BaseModel):
    cheaper: list[OfferLite] = Field(default_factory=list)
    pricier: list[OfferLite] = Field(default_factory=list)


class AnalyzeResult(BaseModel):
    query: str
    region: Literal["BY", "RU"]
    currency: str
    verdict: Literal["good", "fair", "bad"]
    score: int = Field(ge=0, le=100)
    stats: PriceStats
    best_offer: OfferLite
    red_flags: list[RedFlag] = Field(default_factory=list)
    value_analysis: str
    alternatives: AnalyzeAlternatives
    generated_at: datetime


class LLMAnalyzePayload(BaseModel):
    """Only the fields we accept from the LLM. Everything else is ignored."""

    verdict: Literal["good", "fair", "bad"]
    score: int = Field(ge=0, le=100)
    red_flags: list[RedFlag] = Field(default_factory=list)
    value_analysis: str
