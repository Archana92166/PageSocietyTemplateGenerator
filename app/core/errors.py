"""Application-specific exception types."""


class ConfigurationError(RuntimeError):
    """Raised when application configuration cannot be loaded or validated."""
