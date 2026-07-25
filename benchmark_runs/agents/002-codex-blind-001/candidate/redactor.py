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
    """Return a recursive copy with values of sensitive dictionary keys redacted."""
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            normalized_key = key.lower().replace("-", "_") if isinstance(key, str) else None
            if normalized_key in _SENSITIVE_KEYS:
                redacted[key] = _REDACTED
            else:
                redacted[key] = redact_sensitive_values(item)
        return redacted

    if isinstance(value, list):
        return [redact_sensitive_values(item) for item in value]

    if isinstance(value, tuple):
        return tuple(redact_sensitive_values(item) for item in value)

    return value
