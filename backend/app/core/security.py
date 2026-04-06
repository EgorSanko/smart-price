"""JWT token and password hashing utilities."""

import hashlib
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    """Hash password using SHA-256 + salt (simple, reliable)."""
    import secrets

    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${h}"


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against stored hash."""
    if "$" not in hashed:
        return False
    salt, stored_hash = hashed.split("$", 1)
    h = hashlib.sha256(f"{salt}{plain}".encode()).hexdigest()
    return h == stored_hash


def create_access_token(subject: int, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return jwt.encode(
        {"sub": str(subject), "exp": expire, "type": "access"},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(subject: int) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(subject), "exp": expire, "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
