"""Utilities for safely redacting sensitive values from nested telemetry."""

_REDACTED = "[REDACTED]"
_SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "access_token",
    "api_key",
    "authorization",
    "cookie",
}


def redact_sensitive_values(value):
    """Return a recursively copied value with sensitive dictionary values redacted."""
    if isinstance(value, dict):
        return {
            key: (
                _REDACTED
                if isinstance(key, str)
                and key.lower().replace("-", "_") in _SENSITIVE_KEYS
                else redact_sensitive_values(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [redact_sensitive_values(item) for item in value]

    if isinstance(value, tuple):
        return tuple(redact_sensitive_values(item) for item in value)

    return value
