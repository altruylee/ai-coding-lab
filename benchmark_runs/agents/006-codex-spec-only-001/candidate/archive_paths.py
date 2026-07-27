import ntpath
import re


_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")


def normalize_archive_members(names):
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
            raise ValueError("absolute and UNC paths are not allowed")
        if _DRIVE_PREFIX.match(name) or ntpath.splitdrive(name)[0]:
            raise ValueError("drive-prefixed paths are not allowed")

        segments = []
        for segment in re.split(r"[/\\]", name):
            if not segment or segment == ".":
                continue
            if segment == "..":
                raise ValueError("parent path segments are not allowed")
            segments.append(segment)

        if not segments:
            raise ValueError("archive member name normalizes to an empty path")

        normalized = "/".join(segments)
        comparison_key = normalized.casefold()
        if comparison_key in seen:
            raise ValueError("duplicate normalized archive member name")

        seen.add(comparison_key)
        normalized_names.append(normalized)

    return sorted(normalized_names)
