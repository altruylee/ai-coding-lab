"""Select messages for a token budget."""


def select_context_messages(messages, budget):
    """Greedily keep messages from the beginning."""

    selected = []
    used = 0
    for message in messages:
        if used + message["tokens"] <= budget:
            selected.append(message)
            used += message["tokens"]
    return selected
