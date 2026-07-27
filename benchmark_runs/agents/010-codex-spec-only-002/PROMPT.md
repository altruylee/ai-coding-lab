# Task 010 blind-run prompt

You are the isolated participant in a public coding-agent benchmark. This is a
blind run.

## Hard boundary

- Use only this prompt.
- Do not call tools.
- Do not read or write the filesystem.
- Do not access the network.
- You have not been given, and must not seek, any reference implementation or
  tests.
- Return only the complete contents of `text_edits.py` in one Python code
  block, followed by the exact attestation line.
- Do not include hidden reasoning.

## Task

Implement `apply_text_edits(source, edits)` in `text_edits.py`.

Every edit is a dictionary containing exactly `start`, `end`, and `text`.
Offsets refer to the original source, not text produced by earlier edits. The
interval is half-open: `[start, end)`.

Requirements:

- Require `source` to be a string.
- Require `edits` to be a list or tuple.
- Require integer `start` and `end` offsets; booleans are invalid.
- Require `text` to be a string.
- Require `0 <= start <= end <= len(source)`.
- Accept edits in any input order and apply them by original offset.
- Allow adjacent edits and insertions at replacement boundaries.
- Reject overlapping replacement ranges.
- Reject multiple zero-width insertions at the same position.
- Reject missing or extra edit fields.
- Return `source` unchanged for an empty edit collection.
- Raise `ValueError` for invalid input.
- Do not mutate `edits`.
- Only `text_edits.py` may be changed.
- Use Python 3.11+ and the standard library only.

Required final attestation:

`ATTESTATION: no tools, filesystem, network, tests, or reference accessed`
