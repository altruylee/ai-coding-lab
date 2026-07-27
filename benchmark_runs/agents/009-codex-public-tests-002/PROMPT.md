# Task 009 blind-run prompt with public test descriptions

You are the isolated participant in a public coding-agent benchmark. This is a
blind run.

## Hard boundary

- Use only this prompt and the public test descriptions below.
- Do not call tools.
- Do not read or write the filesystem.
- Do not access the network.
- You have not been given, and must not seek, any reference implementation.
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
- Raise `ValueError` for invalid input.
- Only `context_window.py` may be changed.
- Use Python 3.11+ and the standard library only.

Public test descriptions:

1. All system messages and the latest user are retained, then recent optional
   messages are selected within budget and returned chronologically.
2. An oversized recent optional message is skipped while a smaller older one
   can still be selected.
3. Multiple system messages are mandatory even when separated by optional
   messages.
4. Mandatory overflow raises exactly
   `ValueError("mandatory messages exceed budget")`.
5. `None` collections, boolean or negative budgets, missing fields, invalid
   roles, non-string content, boolean tokens, and zero tokens all raise
   `ValueError`.
6. The result is independent and changing it does not mutate the input.

Required final attestation:

`ATTESTATION: no tools, filesystem, network, or reference accessed`
