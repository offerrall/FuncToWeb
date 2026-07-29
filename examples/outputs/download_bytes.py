"""Bytes are built in memory, and they need an explicit filename."""

from typing import Annotated

from func_to_web import Download, run


def export_notes(
    title: str,
    body: str,
) -> Annotated[bytes, Download("notes.txt")]:
    """Build the whole file in memory and serve it with a fixed name.

    A fixed filename only works because this Download is a single file.
    """
    lines = [title, "=" * len(title), "", body, ""]

    return "\n".join(lines).encode("utf-8")


if __name__ == "__main__":
    run(export_notes, title="Download from memory")
