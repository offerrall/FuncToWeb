"""max_upload_bytes is the transport ceiling of the whole space."""

from pathlib import Path
from typing import Annotated

from func_to_web import IsPathFile, Label, run

CEILING = 2 * 1024 * 1024

ArchiveFile = Annotated[
    str,
    IsPathFile(extensions=(".zip", ".tar.gz")),
    Label("Backup"),
]


def inspect_backup(archive: ArchiveFile, note: str = "") -> str:
    """Report the stored size of an uploaded backup.

    max_upload_bytes is a global transport limit: it caps every single file
    the upload endpoint receives, for every function of the space, and it is
    counted per request, so a form with two files checks each one on its
    own. It is unrelated to the min_size and max_size of a field, which
    belong to the parameter and are decided when the call is built.
    """
    size = Path(archive).stat().st_size
    tail = f" ({note})" if note else ""

    return f"{size} bytes stored, ceiling is {CEILING} bytes{tail}"


if __name__ == "__main__":
    run(inspect_backup, title="Upload limit", max_upload_bytes=CEILING)
