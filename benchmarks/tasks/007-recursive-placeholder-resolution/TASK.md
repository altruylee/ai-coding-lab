# Task 007 — Resolve placeholders in nested configuration

Implement `resolve_placeholders(value, env)` in `placeholders.py`.

Placeholders use `${NAME}` syntax, where `NAME` matches
`[A-Z_][A-Z0-9_]*`. A doubled dollar sign escapes a placeholder:
`$${NAME}` becomes the literal text `${NAME}`.

## Requirements

- Recursively process strings inside dictionaries, lists, and tuples.
- Preserve dictionary, list, and tuple container types.
- Replace multiple placeholders inside one string.
- Leave strings without placeholders unchanged.
- Resolve only from the supplied `env` dictionary.
- If variables are missing, raise one deterministic
  `ValueError("missing variables: NAME1, NAME2")` containing sorted unique
  names.
- Reject malformed placeholder syntax, including unclosed `${...}` and names
  outside the declared pattern.
- Require `env` to be a dictionary of string keys and string values.
- Require all input dictionary keys to be strings.
- Do not mutate `value` or `env`.

Only `placeholders.py` may be changed.
