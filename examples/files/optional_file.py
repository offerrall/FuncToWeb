"""An optional file: None is a valid value and the widget starts empty."""

from pathlib import Path
from typing import Annotated

from func_to_web import FileHint, Label, OptionalToggle, run

TextFile = Annotated[str, FileHint(extensions=(".txt", ".md"))]

Attachment = Annotated[
    TextFile | None,
    OptionalToggle(False),
    Label("Attachment"),
]


def send_note(body: str, attachment: Attachment = None) -> str:
    """Compose a note that may or may not carry an attached document.

    An optional file field transports None when nothing is chosen, so the
    parameter is either a local path or None and never an empty string. No
    upload happens for the None branch: there are no bytes to move.
    """
    if attachment is None:
        return f"{body}\n(no attachment)"

    content = Path(attachment).read_text(encoding="utf-8")

    return f"{body}\n(attached {len(content)} characters)"


if __name__ == "__main__":
    run(send_note, title="Optional file")
