"""min_size and max_size bound the file itself, and are checked twice."""

from pathlib import Path
from typing import Annotated

from func_to_web import Description, IsPathFile, Label, Max, Min, run

MINIMUM = 100

MAXIMUM = 2 * 1024 * 1024

DataFile = Annotated[
    str,
    IsPathFile(extensions=(".csv",), min_size=MINIMUM, max_size=MAXIMUM),
    Label("Table"),
    Description("Between 100 bytes and 2 MB of comma separated values"),
]


def preview_table(
    table: DataFile,
    rows: Annotated[int, Min(1), Max(20), Label("Rows to show")] = 3,
) -> str:
    """Show the first rows of a size bounded CSV file.

    The bound is enforced at two independent points. The browser weighs the
    chosen file before uploading it, so a file outside the bound never leaves
    the machine and the transfer is saved. The core then weighs the real file
    that arrived, when it builds the arguments: that second measurement is
    the verdict, it answers 422 before the function runs, and no hand written
    HTTP call can skip it.
    """
    lines = Path(table).read_text(encoding="utf-8").splitlines()

    return "\n".join(lines[:rows]) or "empty table"


if __name__ == "__main__":
    run(preview_table, title="File size")
