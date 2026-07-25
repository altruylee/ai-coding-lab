# Task 010 — Apply non-overlapping text edits

Implement `apply_text_edits(source, edits)` in `text_edits.py`.

Every edit is a dictionary containing exactly:

```python
{"start": 0, "end": 4, "text": "replacement"}
```

Offsets refer to the original `source`, not to text produced by earlier edits.
The interval is half-open: `[start, end)`.

## Requirements

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

Only `text_edits.py` may be changed.
