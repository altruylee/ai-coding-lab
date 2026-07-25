"""Validate archive paths."""

import re


_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")


def normalize_archive_members(names):
    """Return deterministic safe archive member names."""

    if not isinstance(names, (list, tuple)):
        raise ValueError("names must be a list or tuple")

    normalized_names = []
    seen = set()
    for name in names:
        if not isinstance(name, str) or not name:
            raise ValueError("archive names must be non-empty strings")
        if "\x00" in name:
            raise ValueError("archive names cannot contain NUL")

        portable = name.replace("\\", "/")
        if portable.startswith("/") or _DRIVE_PREFIX.match(portable):
            raise ValueError(f"absolute archive path: {name}")

        parts = portable.split("/")
        if ".." in parts:
            raise ValueError(f"parent traversal in archive path: {name}")
        kept = [part for part in parts if part not in {"", "."}]
        if not kept:
            raise ValueError(f"empty archive path: {name}")

        normalized = "/".join(kept)
        folded = normalized.casefold()
        if folded in seen:
            raise ValueError(f"duplicate archive path: {normalized}")
        seen.add(folded)
        normalized_names.append(normalized)

    return sorted(normalized_names)
