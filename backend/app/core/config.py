"""Core config — re-exports from app.config for backwards compatibility."""

from app.config import Settings, get_settings, settings


__all__ = ["Settings", "get_settings", "settings"]
