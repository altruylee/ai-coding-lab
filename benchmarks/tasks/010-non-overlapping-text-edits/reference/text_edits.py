"""Apply text edits."""


_FIELDS = {"start", "end", "text"}


def apply_text_edits(source, edits):
    """Apply validated edits using offsets from the original source."""

    if not isinstance(source, str):
        raise ValueError("source must be a string")
    if not isinstance(edits, (list, tuple)):
        raise ValueError("edits must be a list or tuple")

    normalized = []
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != _FIELDS:
            raise ValueError("edits must contain exactly start, end, text")
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
            raise ValueError("edit offsets are outside source")
        normalized.append((start, end, text))

    normalized.sort(key=lambda item: (item[0], item[1]))
    for index in range(1, len(normalized)):
        previous = normalized[index - 1]
        current = normalized[index]
        if current[0] < previous[1]:
            raise ValueError("overlapping edits")
        if (
            current[0] == current[1]
            and previous[0] == previous[1]
            and current[0] == previous[0]
        ):
            raise ValueError("duplicate insertion position")

    result = source
    for start, end, text in reversed(normalized):
        result = result[:start] + text + result[end:]
    return result
