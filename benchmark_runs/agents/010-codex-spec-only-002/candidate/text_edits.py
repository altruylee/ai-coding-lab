"""Utilities for applying edits to text."""


def apply_text_edits(source, edits):
    """Apply validated edits whose offsets refer to the original source."""
    if not isinstance(source, str):
        raise ValueError("source must be a string")
    if not isinstance(edits, (list, tuple)):
        raise ValueError("edits must be a list or tuple")
    if not edits:
        return source

    required_fields = {"start", "end", "text"}
    validated = []

    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != required_fields:
            raise ValueError(
                "each edit must contain exactly start, end, and text"
            )

        start = edit["start"]
        end = edit["end"]
        text = edit["text"]

        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
        ):
            raise ValueError("start and end must be integers")
        if not isinstance(text, str):
            raise ValueError("text must be a string")
        if not 0 <= start <= end <= len(source):
            raise ValueError("edit offsets are out of bounds")

        validated.append((start, end, text))

    validated.sort(key=lambda item: (item[0], item[1]))

    insertion_positions = set()
    previous_replacement_start = None
    previous_replacement_end = None

    for start, end, _ in validated:
        if start == end:
            if start in insertion_positions:
                raise ValueError("multiple insertions at the same position")
            insertion_positions.add(start)

            if (
                previous_replacement_end is not None
                and previous_replacement_start < start < previous_replacement_end
            ):
                raise ValueError("an insertion overlaps a replacement range")
        else:
            if (
                previous_replacement_end is not None
                and start < previous_replacement_end
            ):
                raise ValueError("replacement ranges overlap")
            previous_replacement_start = start
            previous_replacement_end = end

    parts = []
    cursor = 0

    for start, end, text in validated:
        parts.append(source[cursor:start])
        parts.append(text)
        if end > cursor:
            cursor = end

    parts.append(source[cursor:])
    return "".join(parts)
