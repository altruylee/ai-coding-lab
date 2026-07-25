# Task 002 blind-run prompt

You are the isolated participant in a public coding-agent benchmark. This is a
blind run.

## Hard boundary

- Use only the task text and public test descriptions in this prompt.
- Do not call any tools.
- Do not read or write the filesystem.
- Do not access the network.
- You have not been given, and must not seek, any reference implementation.
- Return only the complete contents of `redactor.py` and the required
  attestation.
- Do not include hidden reasoning.

## Task

Implement `redact_sensitive_values(value)` in `redactor.py`.

Requirements:

- Recursively copy dictionaries, lists, and tuples.
- Treat dictionary keys case-insensitively.
- Normalize `-` to `_` when comparing keys.
- Replace values for these exact normalized keys with `"[REDACTED]"`:
  `password`, `secret`, `token`, `access_token`, `api_key`, `authorization`,
  and `cookie`.
- Do not redact partial matches such as `token_count` or `secretary`.
- Recurse through values under non-sensitive keys, including non-string keys.
- Preserve scalar values and container types.
- Do not mutate the input.
- Only `redactor.py` may be changed.
- Use Python 3.11+ and the standard library only.

Public test descriptions:

1. Top-level exact keys `password`, `secret`, and `token` are redacted.
2. Nested `Authorization`, `Cookie`, and `api-key` values inside dictionaries
   and lists are redacted.
3. A tuple containing `ACCESS-TOKEN`, `API_KEY`, and `PASSWORD` remains a tuple
   and all three values are redacted.
4. `token_count`, `secretary`, and `monkey` are preserved.
5. Values under a non-string dictionary key are recursively copied and
   redacted; the original nested input is unchanged and returned dictionaries
   are new objects.
6. Scalars `None`, booleans, integers, floats, and ordinary strings are
   preserved.

Required final attestation:

`ATTESTATION: no tools, filesystem, network, or reference accessed`
