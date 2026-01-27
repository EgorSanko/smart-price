"""Custom application exceptions.

All custom exceptions inherit from AppException for unified handling.
"""

from typing import Any


class AppException(Exception):
    """Base exception for all application errors.

    Attributes:
        message: Human-readable error message.
        code: Machine-readable error code.
        details: Additional error context.
    """

    def __init__(
        self,
        message: str = "An error occurred",
        code: str = "APP_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found exception.

    Example:
        >>> raise NotFoundError(resource="Product", id=123)
        NotFoundError: Product with id=123 not found
    """

    def __init__(
        self,
        resource: str,
        id: int | str | None = None,
        **kwargs: Any,
    ) -> None:
        identifier = f" with id={id}" if id else ""
        message = f"{resource}{identifier} not found"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            details={"resource": resource, "id": id, **kwargs},
        )


class ValidationError(AppException):
    """Data validation error.

    Example:
        >>> raise ValidationError(field="price", reason="must be positive")
    """

    def __init__(
        self,
        message: str = "Validation error",
        field: str | None = None,
        reason: str | None = None,
        **kwargs: Any,
    ) -> None:
        if field and reason:
            message = f"Validation error on '{field}': {reason}"
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, "reason": reason, **kwargs},
        )


class DatabaseError(AppException):
    """Database operation error.

    Used for wrapping SQLAlchemy errors with additional context.
    """

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details={"operation": operation, **kwargs},
        )


class ExternalServiceError(AppException):
    """External service (scraper, API) error.

    Example:
        >>> raise ExternalServiceError(service="ozon", reason="rate limited")
    """

    def __init__(
        self,
        service: str,
        reason: str = "Service unavailable",
        **kwargs: Any,
    ) -> None:
        message = f"External service '{service}' error: {reason}"
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "reason": reason, **kwargs},
        )


class AuthenticationError(AppException):
    """Authentication failure."""

    def __init__(
        self,
        message: str = "Authentication failed",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            details=kwargs,
        )


class AuthorizationError(AppException):
    """Authorization failure (insufficient permissions)."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            details={"required_permission": required_permission, **kwargs},
        )


class RateLimitError(AppException):
    """Rate limit exceeded."""

    def __init__(
        self,
        retry_after: int | None = None,
        **kwargs: Any,
    ) -> None:
        message = "Rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(
            message=message,
            code="RATE_LIMIT_ERROR",
            details={"retry_after": retry_after, **kwargs},
        )
