"""Deduplicate events."""


def deduplicate_events(events):
    """Keep the first event for each ID."""

    result = []
    seen = set()
    for event in events:
        if event["id"] not in seen:
            seen.add(event["id"])
            result.append(event)
    return result
