"""An optional download: None replaces the whole file, never one inside it."""

from pathlib import Path
from tempfile import mkdtemp
from typing import Annotated

from func_to_web import Download, Max, Min, run

Receipt = Annotated[Path, Download()] | None


def issue_receipt(
    reference: str,
    units: Annotated[int, Min(0), Max(100)],
) -> tuple[str, Receipt]:
    """Return a summary and, only when something was sold, a receipt file.

    None can replace a whole Download output, so the second position is a
    file on one run and, on the next, the "Done" that any None produces.
    What it cannot do is stand for one file inside a Download: the union
    wraps the annotated type, not one of its branches, and mixing a download
    branch with an ordinary one is refused when the WebFunction is built,
    because nothing in the returned value says which branch it came from.
    """
    if units == 0:
        return f"{reference}: nothing sold", None

    path = Path(mkdtemp()) / f"{reference}.txt"

    with path.open("w", encoding="utf-8") as file:
        file.write(f"{reference}\n{units} units\n")

    return f"{reference}: {units} units", path


if __name__ == "__main__":
    run(issue_receipt, title="Optional download")
