"""A Path marked with Download is served as a file instead of as text."""

from pathlib import Path
from tempfile import mkdtemp
from typing import Annotated

from func_to_web import Download, run


def export_report(
    title: str,
    rows: int,
) -> Annotated[Path, Download()]:
    """Write a CSV in a temporary folder and offer it for download.

    Without a filename the download takes the name of the returned path.
    """
    path = Path(mkdtemp()) / "report.csv"

    with path.open("w", encoding="utf-8", newline="") as file:
        file.write("index,title\n")

        for index in range(1, rows + 1):
            file.write(f"{index},{title}\n")

    return path


if __name__ == "__main__":
    run(export_report, title="Download a file")
