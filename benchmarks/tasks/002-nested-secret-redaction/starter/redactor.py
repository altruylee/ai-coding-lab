"""Redact sensitive values from agent telemetry."""


SENSITIVE_KEYS = {"password", "secret", "token"}


def redact_sensitive_values(value: object) -> object:
    """Return a shallow redacted copy of a dictionary."""

    if not isinstance(value, dict):
        return value
    return {
        key: "[REDACTED]" if key in SENSITIVE_KEYS else item
        for key, item in value.items()
    }
