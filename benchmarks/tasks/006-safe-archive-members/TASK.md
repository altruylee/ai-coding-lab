# Task 006 — Validate archive member paths

Implement `normalize_archive_members(names)` in `archive_paths.py`.

The function prepares untrusted ZIP-style member names for safe extraction.
It validates names only; it does not access the filesystem.

## Requirements

- Accept a list or tuple of non-empty strings.
- Treat both `/` and `\` as separators.
- Remove empty and `.` path segments.
- Return normalized `/`-separated names in lexicographic order.
- Reject names containing a NUL byte.
- Reject Unix absolute paths, UNC paths, and Windows drive-prefixed paths.
- Reject any `..` segment, even when another segment would appear to cancel it.
- Reject names that normalize to an empty path.
- Reject duplicate normalized names using case-insensitive comparison.
- Raise `ValueError` for invalid input.
- Do not mutate `names`.

Only `archive_paths.py` may be changed.
