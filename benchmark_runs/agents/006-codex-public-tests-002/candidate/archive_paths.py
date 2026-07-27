"""Utilities for validating and normalizing archive member paths."""

import re


_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")


def normalize_archive_members(names):
    """Return validated archive member names in normalized, sorted form."""
    if not isinstance(names, (list, tuple)):
        raise ValueError("names must be a list or tuple")

    normalized_names = []
    seen = set()

    for name in names:
        if not isinstance(name, str) or not name:
            raise ValueError("archive member names must be non-empty strings")
        if "\x00" in name:
            raise ValueError("archive member names must not contain NUL bytes")
        if name.startswith(("/", "\\")):
            raise ValueError("absolute archive member paths are not allowed")
        if _DRIVE_PREFIX.match(name):
            raise ValueError(
                "drive-prefixed archive member paths are not allowed"
            )

        segments = []
        for segment in name.replace("\\", "/").split("/"):
            if not segment or segment == ".":
                continue
            if segment == "..":
                raise ValueError("parent path segments are not allowed")
            segments.append(segment)

        normalized = "/".join(segments)
        if not normalized:
            raise ValueError("archive member name normalizes to an empty path")
        if _DRIVE_PREFIX.match(normalized):
            raise ValueError(
                "drive-prefixed archive member paths are not allowed"
            )

        comparison_key = normalized.casefold()
        if comparison_key in seen:
            raise ValueError("duplicate archive member name")
        seen.add(comparison_key)
        normalized_names.append(normalized)

    return sorted(normalized_names)
