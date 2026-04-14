"""Database models."""

from app.db.models.alert import PriceAlert, SearchHistory
from app.db.models.category import Category
from app.db.models.chat import ChatMessage, ChatSession
from app.db.models.cheaper import CheaperSearch, CheaperStatus
from app.db.models.marketplace import Marketplace
from app.db.models.payment import Payment
from app.db.models.price_history import PriceHistory
from app.db.models.product import Product
from app.db.models.product_match import ProductMatch
from app.db.models.scraping_job import ScrapingJob
from app.db.models.user import User


__all__ = [
    "Marketplace",
    "Category",
    "Product",
    "PriceHistory",
    "ProductMatch",
    "User",
    "PriceAlert",
    "SearchHistory",
    "ChatSession",
    "ChatMessage",
    "Payment",
    "ScrapingJob",
    "CheaperSearch",
    "CheaperStatus",
]
