"""Utilities for validating and normalizing archive member paths."""


def normalize_archive_members(names):
    """Return safe, portable archive member names in lexicographic order."""
    if not isinstance(names, (list, tuple)):
        raise ValueError("names must be a list or tuple")

    normalized = []
    seen = set()

    for name in names:
        if not isinstance(name, str) or not name:
            raise ValueError("archive member names must be non-empty strings")
        if "\x00" in name:
            raise ValueError("archive member names must not contain NUL bytes")
        if name.startswith(("/", "\\")):
            raise ValueError("absolute archive member paths are not allowed")

        parts = []
        for segment in name.replace("\\", "/").split("/"):
            if not segment or segment == ".":
                continue
            if segment == "..":
                raise ValueError("parent path segments are not allowed")
            parts.append(segment)

        if not parts:
            raise ValueError("archive member name normalizes to an empty path")

        first = parts[0]
        if (
            len(first) >= 2
            and first[1] == ":"
            and ("A" <= first[0] <= "Z" or "a" <= first[0] <= "z")
        ):
            raise ValueError("Windows drive-prefixed paths are not allowed")

        member = "/".join(parts)
        duplicate_key = member.casefold()
        if duplicate_key in seen:
            raise ValueError("duplicate archive member name")
        seen.add(duplicate_key)
        normalized.append(member)

    return sorted(normalized)
