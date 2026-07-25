"""Validate archive paths."""

import posixpath


def normalize_archive_members(names):
    """Normalize member names and reject obvious parent escapes."""

    result = []
    for name in names:
        normalized = posixpath.normpath(name.replace("\\", "/"))
        if normalized.startswith("../"):
            raise ValueError("unsafe archive path")
        result.append(normalized)
    return sorted(result)
