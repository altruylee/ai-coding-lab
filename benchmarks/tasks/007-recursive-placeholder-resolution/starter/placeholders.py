"""Resolve configuration placeholders."""


def resolve_placeholders(value, env):
    """Replace placeholders in a single string."""

    if not isinstance(value, str):
        return value
    for name, replacement in env.items():
        value = value.replace("${" + name + "}", replacement)
    return value
