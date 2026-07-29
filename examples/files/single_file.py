"""One file parameter: the function receives a local path, never bytes."""

from pathlib import Path
from typing import Annotated

from func_to_web import Description, IsPathFile, Label, run

TextFile = Annotated[
    str,
    IsPathFile(extensions=(".txt", ".md")),
    Label("Document"),
    Description("A plain text document to measure"),
]


def count_words(document: TextFile) -> str:
    """Measure an uploaded text document.

    The parameter is a plain str holding the full local path of the already
    stored file, so the function opens it like any other file on disk: it
    knows nothing about HTTP, uploads or where FuncToWeb keeps its storage.
    """
    content = Path(document).read_text(encoding="utf-8")

    lines = content.splitlines()
    words = content.split()

    return (
        f"{len(lines)} lines, {len(words)} words, "
        f"{len(content)} characters"
    )


if __name__ == "__main__":
    run(count_words, title="Single file")
