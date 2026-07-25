# Task 009 — Select messages for a context window

Implement `select_context_messages(messages, budget)` in `context_window.py`.

Each message must contain exactly `role`, `content`, and `tokens`.

## Requirements

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

Only `context_window.py` may be changed.
