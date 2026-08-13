"""min_size and max_size bound the file itself, before it is sent."""

from pathlib import Path
from typing import Annotated

from func_to_web import Description, FileHint, Label, Max, Min, run

MINIMUM = 100

MAXIMUM = 2 * 1024 * 1024

DataFile = Annotated[
    str,
    FileHint(extensions=(".csv",), min_size=MINIMUM, max_size=MAXIMUM),
    Label("Table"),
    Description("Between 100 bytes and 2 MB of comma separated values"),
]


def preview_table(
    table: DataFile,
    rows: Annotated[int, Min(1), Max(20), Label("Rows to show")] = 3,
) -> str:
    """Show the first rows of a size bounded CSV file.

    The bound belongs to the field and travels to the page inside the plan,
    so the browser weighs the file the user just picked and refuses it
    there: a file outside the bound never leaves the machine and the
    transfer is saved. That is the only place it is weighed. Building the
    arguments looks at the extension of the path, never at its length, and
    a file already in storage, chosen by its reference, has no bytes for
    the browser to weigh either, so nothing bounds its size. The one byte
    count the server performs is max_upload_bytes, the ceiling of the
    upload endpoint, which limits the space rather than this field.
    """
    lines = Path(table).read_text(encoding="utf-8").splitlines()

    return "\n".join(lines[:rows]) or "empty table"


if __name__ == "__main__":
    run(preview_table, title="File size")
