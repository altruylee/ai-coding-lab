"""Utilities for applying validated edits to text."""


def apply_text_edits(source, edits):
    """Apply non-conflicting edits whose offsets refer to the original source."""
    if not isinstance(source, str):
        raise ValueError("source must be a string")
    if not isinstance(edits, (list, tuple)):
        raise ValueError("edits must be a list or tuple")

    expected_fields = {"start", "end", "text"}
    normalized = []

    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != expected_fields:
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
            raise ValueError("edit offsets must be integers")
        if not isinstance(text, str):
            raise ValueError("edit text must be a string")
        if not 0 <= start <= end <= len(source):
            raise ValueError("edit offsets are invalid")

        normalized.append((start, end, text))

    if not normalized:
        return source

    replacements = sorted(
        (edit for edit in normalized if edit[0] != edit[1]),
        key=lambda edit: (edit[0], edit[1]),
    )
    insertions = sorted(
        (edit for edit in normalized if edit[0] == edit[1]),
        key=lambda edit: edit[0],
    )

    previous_end = -1
    for start, end, _ in replacements:
        if start < previous_end:
            raise ValueError("replacement ranges overlap")
        previous_end = end

    previous_position = None
    replacement_index = 0
    for position, _, _ in insertions:
        if position == previous_position:
            raise ValueError("multiple insertions at the same position")
        previous_position = position

        while (
            replacement_index < len(replacements)
            and replacements[replacement_index][1] <= position
        ):
            replacement_index += 1
        if replacement_index < len(replacements):
            start, end, _ = replacements[replacement_index]
            if start < position < end:
                raise ValueError(
                    "an insertion cannot be inside a replacement range"
                )

    ordered = sorted(
        normalized,
        key=lambda edit: (
            edit[0],
            0 if edit[0] == edit[1] else 1,
            edit[1],
        ),
    )

    pieces = []
    cursor = 0
    for start, end, text in ordered:
        pieces.append(source[cursor:start])
        pieces.append(text)
        cursor = end

    pieces.append(source[cursor:])
    return "".join(pieces)
