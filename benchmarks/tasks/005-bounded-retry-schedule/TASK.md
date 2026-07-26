# Task 005 — Build a bounded retry schedule

Implement `build_retry_delays(...)` in `retry_schedule.py`.

```python
build_retry_delays(attempts, base_delay, max_delay, jitter)
```

`attempts` includes the initial attempt, so the function returns
`attempts - 1` delays.

## Requirements

- Delay `i` uses `base_delay * 2 ** i`, starting at `i = 0`.
- Cap the unjittered delay at `max_delay`.
- Apply the matching jitter factor as `delay * (1 + jitter[i])`.
- Clamp the adjusted value to the inclusive range `0..max_delay`.
- Round each result to six decimal places and return floats.
- `attempts` must be an integer from 1 through 20; booleans are invalid.
- `base_delay` and `max_delay` must be finite positive numbers, and
  `max_delay >= base_delay`; booleans are invalid.
- `jitter` must be a list or tuple with exactly `attempts - 1` finite numeric
  values in the inclusive range `-0.5..0.5`; booleans are invalid.
- Do not mutate `jitter`.
- Raise `ValueError` for every invalid input.

Only `retry_schedule.py` may be changed.
