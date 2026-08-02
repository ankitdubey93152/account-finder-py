"""Custom Exception Hierarchy for OSINT Account & Digital Footprint Analyzer."""

class OSINTError(Exception):
    """Base exception for all errors raised by the OSINT Analyzer."""
    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail

class PlatformUnavailableError(OSINTError):
    """Raised when a specific target platform is unreachable or returns a server error."""
    pass

class InvalidUsernameError(OSINTError):
    """Raised when a username fails validation constraints before scanning."""
    pass

class RateLimitedError(OSINTError):
    """Raised when request rate limits are hit for a platform or service."""
    pass

class ProviderConfigError(OSINTError):
    """Raised when a third-party API provider is missing required configuration or keys."""
    pass

class UnconfirmedOwnerError(OSINTError):
    """Raised when an email lookup is requested without explicit confirmation of ownership."""
    pass
