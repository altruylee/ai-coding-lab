# Task 009 protocol-deviation prompt

You are the isolated participant in a public coding-agent benchmark. This is a
blind run.

## Hard boundary

- Use only this prompt.
- Do not call tools.
- Do not read or write the filesystem.
- Do not access the network.
- You have not been given, and must not seek, any reference implementation or
  tests.
- Return only the complete contents of `context_window.py` in one Python code
  block, followed by the exact attestation line.
- Do not include hidden reasoning.

## Task

Implement `select_context_messages(messages, budget)` in `context_window.py`.

Each message must contain exactly `role`, `content`, and `tokens`.

Requirements:

- Accept a list or tuple of message dictionaries.
- Roles must be one of `system`, `user`, `assistant`, or `tool`.
- `content` must be a string.
- `tokens` must be a positive integer; booleans are invalid.
- `budget` must be a non-negative integer; booleans are invalid.
- Always retain every system message and the most recent user message, when
  one exists.
- Raise `ValueError("mandatory messages exceed budget")` if those mandatory
  messages do not fit.
- Consider other messages from newest to oldest. Add a message if it fits the
  remaining budget; if it does not fit, continue considering older messages.
- Return selected messages in their original chronological order.
- Deep-copy the result and do not mutate `messages`.
- Reject missing or extra message fields.
- Raise `ValueError` for every invalid input.
- Only `context_window.py` may be changed.
- Use Python 3.11+ and the standard library only.

Required final attestation:

`ATTESTATION: no tools, filesystem, network, tests, or reference accessed`
