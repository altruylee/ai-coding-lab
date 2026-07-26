"""Deduplicate events."""

from copy import deepcopy
import math


def _valid_json(value):
    if value is None or isinstance(value, (bool, str)):
        return True
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_valid_json(child) for child in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _valid_json(child)
            for key, child in value.items()
        )
    return False


def deduplicate_events(events):
    """Return canonical events while rejecting conflicting retries."""

    if not isinstance(events, (list, tuple)):
        raise ValueError("events must be a list or tuple")

    by_id = {}
    conflicts = set()
    required = {"id", "timestamp", "payload"}
    for event in events:
        if not isinstance(event, dict) or set(event) != required:
            raise ValueError("events must contain exactly id, timestamp, payload")
        event_id = event["id"]
        timestamp = event["timestamp"]
        payload = event["payload"]
        if not isinstance(event_id, str) or not event_id:
            raise ValueError("event id must be a non-empty string")
        if (
            not isinstance(timestamp, int)
            or isinstance(timestamp, bool)
            or timestamp < 0
        ):
            raise ValueError("timestamp must be a non-negative integer")
        if not _valid_json(payload):
            raise ValueError("payload must be JSON-compatible")

        previous = by_id.get(event_id)
        if previous is None:
            by_id[event_id] = {
                "id": event_id,
                "timestamp": timestamp,
                "payload": deepcopy(payload),
            }
        elif previous["payload"] != payload:
            conflicts.add(event_id)
        elif timestamp < previous["timestamp"]:
            previous["timestamp"] = timestamp

    if conflicts:
        raise ValueError(f"conflicting event: {min(conflicts)}")
    return sorted(
        (deepcopy(event) for event in by_id.values()),
        key=lambda event: (event["timestamp"], event["id"]),
    )
