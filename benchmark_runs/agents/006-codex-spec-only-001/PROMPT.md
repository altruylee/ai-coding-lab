# Task 006 blind-run prompt

You are the isolated participant in a public coding-agent benchmark. This is a
blind run.

## Hard boundary

- Use only this prompt.
- Do not call tools.
- Do not read or write the filesystem.
- Do not access the network.
- You have not been given, and must not seek, any reference implementation or
  tests.
- Return only the complete contents of `archive_paths.py` in one Python code
  block, followed by the exact attestation line.
- Do not include hidden reasoning.

## Task

Implement `normalize_archive_members(names)` in `archive_paths.py`.

Requirements:

- Accept a list or tuple of non-empty strings.
- Treat both `/` and backslash as separators.
- Remove empty and `.` path segments.
- Return normalized `/`-separated names in lexicographic order.
- Reject names containing a NUL byte.
- Reject Unix absolute paths, UNC paths, and Windows drive-prefixed paths.
- Reject any `..` segment, even when another segment would appear to cancel
  it.
- Reject names that normalize to an empty path.
- Reject duplicate normalized names using case-insensitive comparison.
- Raise `ValueError` for invalid input.
- Do not mutate `names`.
- Only `archive_paths.py` may be changed.
- Use Python 3.11+ and the standard library only.

Required final attestation:

`ATTESTATION: no tools, filesystem, network, tests, or reference accessed`
