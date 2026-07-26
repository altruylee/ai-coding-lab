from copy import deepcopy


def select_context_messages(messages, budget):
    if not isinstance(messages, (list, tuple)):
        raise ValueError("messages must be a list or tuple")
    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
        raise ValueError("budget must be a non-negative integer")

    required_fields = {"role", "content", "tokens"}
    valid_roles = {"system", "user", "assistant", "tool"}
    latest_user_index = None

    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError("each message must be a dictionary")
        if set(message.keys()) != required_fields:
            raise ValueError(
                "each message must contain exactly role, content, and tokens"
            )

        role = message["role"]
        content = message["content"]
        tokens = message["tokens"]

        if role not in valid_roles:
            raise ValueError("invalid message role")
        if not isinstance(content, str):
            raise ValueError("message content must be a string")
        if (
            not isinstance(tokens, int)
            or isinstance(tokens, bool)
            or tokens <= 0
        ):
            raise ValueError("message tokens must be a positive integer")

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
