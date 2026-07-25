"""Resolve configuration placeholders."""

import re


_NAME = re.compile(r"^[A-Z_][A-Z0-9_]*$")


def _resolve_string(text, env, missing):
    result = []
    index = 0
    while index < len(text):
        if text.startswith("$${", index):
            end = text.find("}", index + 3)
            if end == -1:
                raise ValueError("unclosed placeholder")
            name = text[index + 3:end]
            if not _NAME.fullmatch(name):
                raise ValueError(f"invalid placeholder: {name}")
            result.append("${" + name + "}")
            index = end + 1
        elif text.startswith("${", index):
            end = text.find("}", index + 2)
            if end == -1:
                raise ValueError("unclosed placeholder")
            name = text[index + 2:end]
            if not _NAME.fullmatch(name):
                raise ValueError(f"invalid placeholder: {name}")
            if name in env:
                result.append(env[name])
            else:
                missing.add(name)
            index = end + 1
        else:
            result.append(text[index])
            index += 1
    return "".join(result)


def _walk(value, env, missing):
    if isinstance(value, str):
        return _resolve_string(value, env, missing)
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("dictionary keys must be strings")
        return {key: _walk(child, env, missing) for key, child in value.items()}
    if isinstance(value, list):
        return [_walk(child, env, missing) for child in value]
    if isinstance(value, tuple):
        return tuple(_walk(child, env, missing) for child in value)
    return value


def resolve_placeholders(value, env):
    """Resolve placeholders recursively from an explicit environment."""

    if (
        not isinstance(env, dict)
        or any(not isinstance(key, str) for key in env)
        or any(not isinstance(child, str) for child in env.values())
    ):
        raise ValueError("env must contain string keys and values")

    missing = set()
    result = _walk(value, env, missing)
    if missing:
        raise ValueError("missing variables: " + ", ".join(sorted(missing)))
    return result
