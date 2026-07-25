# Task 002 spec-only blind-run prompt

You are the isolated participant in a public coding-agent benchmark. This is a
blind, spec-only run.

## Hard boundary

- Use only the task requirements in this prompt. No test descriptions are
  provided.
- Do not call any tools.
- Do not read or write the filesystem.
- Do not access the network.
- You have not been given, and must not seek, any reference implementation or
  tests.
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

Required final attestation:

`ATTESTATION: no tools, filesystem, network, tests, or reference accessed`
