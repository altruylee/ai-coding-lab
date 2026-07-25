"""Redact sensitive values from agent telemetry."""


SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "access_token",
    "api_key",
    "authorization",
    "cookie",
}


def _normalized_key(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value.casefold().replace("-", "_")


def redact_sensitive_values(value: object) -> object:
    """Return a recursively redacted copy of supported telemetry values."""

    if isinstance(value, dict):
        return {
            key: (
                "[REDACTED]"
                if _normalized_key(key) in SENSITIVE_KEYS
                else redact_sensitive_values(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive_values(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive_values(item) for item in value)
    return value
