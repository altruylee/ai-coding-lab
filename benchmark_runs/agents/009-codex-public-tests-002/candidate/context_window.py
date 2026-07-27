"""Utilities for selecting messages within a token budget."""

from copy import deepcopy
from typing import Any


_VALID_ROLES = {"system", "user", "assistant", "tool"}
_REQUIRED_FIELDS = {"role", "content", "tokens"}


def select_context_messages(
    messages: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    budget: int,
) -> list[dict[str, Any]]:
    """Select messages that fit within *budget*, preserving mandatory context."""
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
        raise ValueError("invalid budget")

    if not isinstance(messages, (list, tuple)):
        raise ValueError("invalid messages")

    latest_user_index: int | None = None

    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError("invalid message")
        if set(message.keys()) != _REQUIRED_FIELDS:
            raise ValueError("invalid message fields")

        role = message["role"]
        content = message["content"]
        tokens = message["tokens"]

        if role not in _VALID_ROLES:
            raise ValueError("invalid role")
        if not isinstance(content, str):
            raise ValueError("invalid content")
        if (
            isinstance(tokens, bool)
            or not isinstance(tokens, int)
            or tokens <= 0
        ):
            raise ValueError("invalid tokens")

        if role == "user":
            latest_user_index = index

    mandatory_indices = {
        index
        for index, message in enumerate(messages)
        if message["role"] == "system"
    }
    if latest_user_index is not None:
        mandatory_indices.add(latest_user_index)

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
