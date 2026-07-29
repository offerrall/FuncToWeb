"""A dataclass field can be a file, and a list of them is a table of rows."""

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from func_to_web import IsPathFile, Label, Max, Min, run

TextFile = Annotated[str, IsPathFile(extensions=(".txt", ".md"))]


@dataclass
class Attachment:
    """One document of a bundle, with the name it is filed under."""

    document: TextFile
    label: Annotated[str, Min(1), Max(20)] = "notes"


def build_bundle(
    title: Annotated[str, Min(3), Max(40)],
    items: Annotated[list[Attachment], Min(1), Max(4), Label("Attachments")],
) -> str:
    """Build an index of the documents carried by a list of dataclasses.

    Each row of the list is a small form with its own file widget, and the
    dataclass arrives fully built: item.document is already a local path.
    """
    lines = [
        f"{item.label}: {len(Path(item.document).read_bytes())} bytes"
        for item in items
    ]

    return "\n".join([f"{title} ({len(items)} attachments)", *lines])


if __name__ == "__main__":
    run(build_bundle, title="Dataclass with file")
