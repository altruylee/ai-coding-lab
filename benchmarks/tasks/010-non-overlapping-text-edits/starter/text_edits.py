"""Apply text edits."""


def apply_text_edits(source, edits):
    """Apply edits sequentially in their supplied order."""

    for edit in edits:
        source = (
            source[: edit["start"]]
            + edit["text"]
            + source[edit["end"] :]
        )
    return source
