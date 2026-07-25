"""Select messages for a token budget."""

from copy import deepcopy


_ROLES = {"system", "user", "assistant", "tool"}
_FIELDS = {"role", "content", "tokens"}


def select_context_messages(messages, budget):
    """Select mandatory and recent messages within a token budget."""

    if not isinstance(messages, (list, tuple)):
        raise ValueError("messages must be a list or tuple")
    if (
        not isinstance(budget, int)
        or isinstance(budget, bool)
        or budget < 0
    ):
        raise ValueError("budget must be a non-negative integer")

    for item in messages:
        if not isinstance(item, dict) or set(item) != _FIELDS:
            raise ValueError("messages must contain exactly role, content, tokens")
        if item["role"] not in _ROLES:
            raise ValueError("invalid message role")
        if not isinstance(item["content"], str):
            raise ValueError("message content must be a string")
        if (
            not isinstance(item["tokens"], int)
            or isinstance(item["tokens"], bool)
            or item["tokens"] <= 0
        ):
            raise ValueError("message tokens must be a positive integer")

    mandatory = {
        index
        for index, item in enumerate(messages)
        if item["role"] == "system"
    }
    latest_user = next(
        (
            index
            for index in range(len(messages) - 1, -1, -1)
            if messages[index]["role"] == "user"
        ),
        None,
    )
    if latest_user is not None:
        mandatory.add(latest_user)

    used = sum(messages[index]["tokens"] for index in mandatory)
    if used > budget:
        raise ValueError("mandatory messages exceed budget")

    selected = set(mandatory)
    for index in range(len(messages) - 1, -1, -1):
        if index in selected:
            continue
        tokens = messages[index]["tokens"]
        if used + tokens <= budget:
            selected.add(index)
            used += tokens

    return [
        deepcopy(messages[index])
        for index in range(len(messages))
        if index in selected
    ]
