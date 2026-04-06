"""Parsers listing endpoint."""

from fastapi import APIRouter

from app.scrapers.manager import get_parsers


router = APIRouter(prefix="/parsers", tags=["parsers"])


@router.get("")
async def list_parsers() -> dict:
    """List all available marketplace parsers."""
    return get_parsers()
