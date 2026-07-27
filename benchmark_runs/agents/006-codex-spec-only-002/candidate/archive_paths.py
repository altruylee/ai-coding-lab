"""Utilities for validating and normalizing archive member paths."""

from __future__ import annotations

import re
from typing import Sequence

_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")


def normalize_archive_members(names: list[str] | tuple[str, ...]) -> list[str]:
    """Validate and normalize archive member names."""
    if not isinstance(names, (list, tuple)):
        raise ValueError("names must be a list or tuple")

    normalized_names: list[str] = []
    seen: set[str] = set()

    for name in names:
        if not isinstance(name, str) or not name:
            raise ValueError("archive member names must be non-empty strings")
        if "\x00" in name:
            raise ValueError("archive member names must not contain NUL bytes")
        if name.startswith(("/", "\\")):
            raise ValueError("absolute and UNC paths are not allowed")
        if _DRIVE_PREFIX.match(name):
            raise ValueError("Windows drive-prefixed paths are not allowed")

        segments = name.replace("\\", "/").split("/")
        if ".." in segments:
            raise ValueError("parent-directory segments are not allowed")

        normalized = "/".join(
            segment for segment in segments if segment and segment != "."
        )
        if not normalized:
            raise ValueError("archive member name normalizes to an empty path")

        comparison_key = normalized.casefold()
        if comparison_key in seen:
            raise ValueError("duplicate archive member name")
        seen.add(comparison_key)
        normalized_names.append(normalized)

    return sorted(normalized_names)
