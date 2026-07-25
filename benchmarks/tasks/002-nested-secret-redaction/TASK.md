# Task 002 — Redact nested agent telemetry safely

Implement `redact_sensitive_values(value)` in `redactor.py`.

Agent telemetry often contains nested command arguments, HTTP headers, and tool
results. The function must return a redacted copy without changing the input.

## Requirements

- Recursively copy dictionaries, lists, and tuples.
- Treat dictionary keys case-insensitively.
- Normalize `-` to `_` when comparing keys.
- Replace values for these exact normalized keys with `"[REDACTED]"`:
  - `password`
  - `secret`
  - `token`
  - `access_token`
  - `api_key`
  - `authorization`
  - `cookie`
- Do not redact partial matches such as `token_count` or `secretary`.
- Recurse through values under non-sensitive keys, including non-string keys.
- Preserve scalar values and container types.
- Do not mutate the input.

Only `redactor.py` may be changed.
