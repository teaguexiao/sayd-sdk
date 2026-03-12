"""Custom exceptions for the Sayd SDK."""


class SaydError(Exception):
    """Base exception for all Sayd errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(SaydError):
    """Raised when the API key is invalid or missing."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, status_code=401)


class RateLimitError(SaydError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: float | None = None):
        self.retry_after = retry_after
        super().__init__(message, status_code=429)


class SubscriptionError(SaydError):
    """Raised when the subscription is not active (expired credit, canceled, etc.)."""

    def __init__(self, message: str = "Subscription not active"):
        super().__init__(message, status_code=403)


class SessionError(SaydError):
    """Raised when there's an error with a talk session."""
    pass
