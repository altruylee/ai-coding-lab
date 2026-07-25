# Task 008 — Deduplicate retried events safely

Implement `deduplicate_events(events)` in `events.py`.

Each event must contain exactly:

```python
{"id": "event-id", "timestamp": 123, "payload": ...}
```

## Requirements

- Accept a list or tuple of event dictionaries.
- Require a non-empty string `id`.
- Require a non-negative integer `timestamp`; booleans are invalid.
- Require `payload` to be JSON-compatible: `None`, booleans, finite numbers,
  strings, lists, or dictionaries with string keys.
- Treat repeated IDs with equal payloads as delivery retries and keep the
  earliest timestamp.
- Raise `ValueError("conflicting event: ID")` when one ID has unequal
  payloads.
- Return deep-copied events sorted by `(timestamp, id)`.
- Produce conflict errors independent of input order by reporting the
  lexicographically smallest conflicting ID.
- Reject missing or extra event fields.
- Do not mutate or share mutable payload containers with the input.

Only `events.py` may be changed.
