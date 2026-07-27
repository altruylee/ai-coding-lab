# Task 006 blind-run prompt with public test descriptions

You are the isolated participant in a public coding-agent benchmark. This is a
blind run.

## Hard boundary

- Use only this prompt and the public test descriptions below.
- Do not call tools.
- Do not read or write the filesystem.
- Do not access the network.
- You have not been given, and must not seek, any reference implementation.
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

Public test descriptions:

1. Mixed slash styles, repeated separators, and `.` segments normalize to
   sorted portable paths.
2. Parent segments are rejected at the beginning, middle, and with
   backslashes, even if they appear to cancel.
3. Unix absolute, UNC, and upper- or lower-case Windows drive paths are
   rejected.
4. Empty strings, `.`, `./`, separator-only names, and NUL-containing names
   are rejected.
5. Case-insensitive duplicate normalized paths are rejected.
6. A bare string collection, `None`, and non-string elements are rejected.
7. The supplied name list remains unchanged.

Required final attestation:

`ATTESTATION: no tools, filesystem, network, or reference accessed`
