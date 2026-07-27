def apply_text_edits(source, edits):
    if not isinstance(source, str):
        raise ValueError("source must be a string")
    if not isinstance(edits, (list, tuple)):
        raise ValueError("edits must be a list or tuple")

    validated = []
    insertion_positions = set()
    required_fields = {"start", "end", "text"}

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
            raise ValueError("edit offsets must be integers")
        if not isinstance(text, str):
            raise ValueError("edit text must be a string")
        if not 0 <= start <= end <= len(source):
            raise ValueError("edit offsets are out of bounds")

        if start == end:
            if start in insertion_positions:
                raise ValueError("multiple insertions at the same position")
            insertion_positions.add(start)

        validated.append((start, end, text))

    if not validated:
        return source

    replacements = sorted(
        (edit for edit in validated if edit[0] != edit[1]),
        key=lambda edit: (edit[0], edit[1]),
    )

    previous_end = -1
    for start, end, _ in replacements:
        if start < previous_end:
            raise ValueError("replacement ranges overlap")
        previous_end = end

    for position in insertion_positions:
        for start, end, _ in replacements:
            if start < position < end:
                raise ValueError("insertion overlaps a replacement range")
            if start >= position:
                break

    ordered = sorted(
        validated,
        key=lambda edit: (edit[0], 0 if edit[0] == edit[1] else 1),
    )

    result = []
    cursor = 0
    for start, end, text in ordered:
        result.append(source[cursor:start])
        result.append(text)
        if start != end:
            cursor = end
        else:
            cursor = start

    result.append(source[cursor:])
    return "".join(result)
