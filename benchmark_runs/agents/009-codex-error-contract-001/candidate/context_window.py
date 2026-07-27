"""Utilities for selecting messages within a token budget."""

from copy import deepcopy
from typing import Any


_ALLOWED_ROLES = {"system", "user", "assistant", "tool"}
_REQUIRED_FIELDS = {"role", "content", "tokens"}


def select_context_messages(
    messages: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    budget: int,
) -> list[dict[str, Any]]:
    """Select context messages without exceeding *budget* tokens."""
    if not isinstance(messages, (list, tuple)):
        raise ValueError("messages must be a list or tuple")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
        raise ValueError("budget must be a non-negative integer")

    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("each message must be a dictionary")
        if set(message.keys()) != _REQUIRED_FIELDS:
            raise ValueError(
                "each message must contain exactly role, content, and tokens"
            )

        role = message["role"]
        content = message["content"]
        tokens = message["tokens"]

        if role not in _ALLOWED_ROLES:
            raise ValueError("invalid message role")
        if not isinstance(content, str):
            raise ValueError("message content must be a string")
        if (
            isinstance(tokens, bool)
            or not isinstance(tokens, int)
            or tokens <= 0
        ):
            raise ValueError("message tokens must be a positive integer")

    mandatory_indices = {
        index
        for index, message in enumerate(messages)
        if message["role"] == "system"
    }

    for index in range(len(messages) - 1, -1, -1):
        if messages[index]["role"] == "user":
            mandatory_indices.add(index)
            break

    mandatory_tokens = sum(
        messages[index]["tokens"] for index in mandatory_indices
    )
    if mandatory_tokens > budget:
        raise ValueError("mandatory messages exceed budget")

    selected_indices = set(mandatory_indices)
    remaining_budget = budget - mandatory_tokens

    for index in range(len(messages) - 1, -1, -1):
        if index in selected_indices:
            continue
        token_count = messages[index]["tokens"]
        if token_count <= remaining_budget:
            selected_indices.add(index)
            remaining_budget -= token_count

    return deepcopy(
        [
            message
            for index, message in enumerate(messages)
            if index in selected_indices
        ]
    )
