from __future__ import annotations


class SleeperError(Exception):
    """
    Base class for all Sleeper SDK errors.
    All other exceptions inherit from this.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


# =========================
# HTTP / TRANSPORT ERRORS
# =========================

class SleeperHTTPError(SleeperError):
    """
    Raised when the HTTP layer fails (non-2xx response).
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        body: dict | str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.body = body

    def is_client_error(self) -> bool:
        return 400 <= self.status_code < 500

    def is_server_error(self) -> bool:
        return 500 <= self.status_code < 600


class SleeperRateLimitError(SleeperHTTPError):
    """
    Raised when Sleeper returns HTTP 429.
    """

    def __init__(self, retry_after: int | None = None):
        super().__init__(
            status_code=429,
            message="Rate limited by Sleeper API",
        )
        self.retry_after = retry_after


class SleeperTimeoutError(SleeperHTTPError):
    """
    Raised when request times out.
    """

    def __init__(self, message: str = "Request timed out"):
        super().__init__(status_code=408, message=message)


class SleeperAuthError(SleeperHTTPError):
    """
    Raised when authentication fails (401/403).
    """

    def __init__(self, status_code: int = 401, message: str = "Authentication failed"):
        super().__init__(status_code=status_code, message=message)


# =========================
# GRAPHQL ERRORS
# =========================

class SleeperGraphQLError(SleeperError):
    """
    Raised when GraphQL returns 'errors' in response payload.
    """

    def __init__(self, errors: list[dict]):
        self.errors = errors

        super().__init__(self._format(errors))

    def _format(self, errors: list[dict]) -> str:
        """
        Convert GraphQL errors into readable message.
        Keeps SDK usable while preserving raw structure.
        """
        messages = []

        for err in errors:
            if isinstance(err, dict):
                msg = err.get("message", str(err))
                path = err.get("path")
                if path:
                    messages.append(f"{msg} (path={path})")
                else:
                    messages.append(msg)
            else:
                messages.append(str(err))

        return " | ".join(messages)


# =========================
# VALIDATION / USAGE ERRORS
# =========================

class SleeperValidationError(SleeperError):
    """
    Raised when SDK is called incorrectly.
    (e.g., missing league_id, invalid params)
    """

    pass


class SleeperUnknownOperationError(SleeperError):
    """
    Raised when a mutation/operation does not exist in registry.
    """

    def __init__(self, operation: str):
        super().__init__(f"Unknown Sleeper operation: {operation}")
        self.operation = operation


# =========================
# INTERNAL SDK ERRORS
# =========================

class SleeperTransportError(SleeperError):
    """
    Low-level transport failure (unexpected issues in HTTP layer).
    """

    pass


class SleeperCircuitBreakerError(SleeperError):
    """
    Raised when circuit breaker prevents requests due to instability.
    """

    def __init__(self, message: str = "Circuit breaker open"):
        super().__init__(message)