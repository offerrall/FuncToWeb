"""max_upload_bytes is the transport ceiling of the whole space."""

from pathlib import Path
from typing import Annotated

from func_to_web import FileHint, Label, run

CEILING = 2 * 1024 * 1024

ArchiveFile = Annotated[
    str,
    FileHint(extensions=(".zip", ".tar.gz")),
    Label("Backup"),
]


def inspect_backup(archive: ArchiveFile, note: str = "") -> str:
    """Report the stored size of an uploaded backup.

    max_upload_bytes is a global transport limit: it caps every single file
    the upload endpoint receives, for every function of the space, and it is
    counted per request, so a form with two files checks each one on its
    own. Real bytes are counted as they arrive, which is why it is the one
    size limit the server itself enforces. It is unrelated to the min_size
    and max_size of a field: those belong to the parameter and are applied
    by the browser to the file it is about to send.
    """
    size = Path(archive).stat().st_size
    tail = f" ({note})" if note else ""

    return f"{size} bytes stored, ceiling is {CEILING} bytes{tail}"


if __name__ == "__main__":
    run(inspect_backup, title="Upload limit", max_upload_bytes=CEILING)
