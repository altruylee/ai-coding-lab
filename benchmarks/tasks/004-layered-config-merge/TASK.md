# Task 004 — Merge layered configuration safely

Implement `merge_config_layers(layers)` in `config_merge.py`.

The input is an ordered list or tuple of configuration dictionaries. Later
layers override earlier layers.

## Requirements

- Recursively merge dictionaries.
- Treat `None` in a later layer as deletion of that key.
- Replace lists, tuples, strings, numbers, and booleans instead of merging
  them.
- If a dictionary replaces an earlier scalar, merge it into an empty mapping.
- Return dictionaries with lexicographically ordered keys at every depth.
- Deep-copy retained values so the result shares no mutable containers with
  the input.
- Accept an empty layer collection and return `{}`.
- Raise `ValueError` when:
  - `layers` is not a list or tuple;
  - a layer is not a dictionary;
  - any dictionary key at any depth is not a non-empty string.
- Do not mutate any input layer.

Only `config_merge.py` may be changed.
