# Task 010 blind-run prompt with public test descriptions

You are the isolated participant in a public coding-agent benchmark. This is a
blind run.

## Hard boundary

- Use only this prompt and the public test descriptions below.
- Do not call tools.
- Do not read or write the filesystem.
- Do not access the network.
- You have not been given, and must not seek, any reference implementation.
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

Public test descriptions:

1. Three unordered replacements are applied using original offsets.
2. Deletion, replacement, and end insertion work together.
3. Adjacent replacements and an insertion at their shared boundary are
   allowed.
4. Overlapping replacements and duplicate insertion positions raise
   `ValueError`.
5. Invalid source/edit collections, missing or extra fields, boolean indices,
   out-of-range or reversed offsets, and non-string replacement text raise
   `ValueError`.
6. Empty edits return the original source and the supplied edits remain
   unchanged.

Required final attestation:

`ATTESTATION: no tools, filesystem, network, or reference accessed`
