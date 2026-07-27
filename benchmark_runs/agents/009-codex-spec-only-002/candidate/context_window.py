"""Utilities for selecting messages within a token budget."""

from copy import deepcopy
from typing import Any


_ALLOWED_ROLES = {"system", "user", "assistant", "tool"}
_REQUIRED_FIELDS = {"role", "content", "tokens"}


def select_context_messages(
    messages: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    budget: int,
) -> list[dict[str, Any]]:
    """Select messages within *budget*, preserving mandatory context."""
    if not isinstance(messages, (list, tuple)):
        raise TypeError("messages must be a list or tuple")
    if isinstance(budget, bool) or not isinstance(budget, int):
        raise TypeError("budget must be a non-negative integer")
    if budget < 0:
        raise ValueError("budget must be a non-negative integer")

    for message in messages:
        if not isinstance(message, dict):
            raise TypeError("each message must be a dictionary")
        if set(message) != _REQUIRED_FIELDS:
            raise ValueError(
                "each message must contain exactly role, content, and tokens"
            )
        if message["role"] not in _ALLOWED_ROLES:
            raise ValueError("invalid message role")
        if not isinstance(message["content"], str):
            raise TypeError("content must be a string")
        tokens = message["tokens"]
        if isinstance(tokens, bool) or not isinstance(tokens, int):
            raise TypeError("tokens must be a positive integer")
        if tokens <= 0:
            raise ValueError("tokens must be a positive integer")

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
        if index in mandatory_indices:
            continue
        tokens = messages[index]["tokens"]
        if tokens <= remaining_budget:
            selected_indices.add(index)
            remaining_budget -= tokens

    return deepcopy(
        [
            message
            for index, message in enumerate(messages)
            if index in selected_indices
        ]
    )
