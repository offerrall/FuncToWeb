"""Accepted extensions: the tuple declared by IsPathFile is the filter."""

from pathlib import Path
from typing import Annotated

from func_to_web import IsPathFile, Label, run

ImageFile = Annotated[
    str,
    IsPathFile(extensions=(".png", ".jpg", ".jpeg")),
    Label("Picture"),
]

ArchiveFile = Annotated[
    str,
    IsPathFile(extensions=(".tar.gz",)),
    Label("Compressed bundle"),
]

AnyFile = Annotated[str, IsPathFile(), Label("Anything else")]


def describe_uploads(
    picture: ImageFile,
    bundle: ArchiveFile,
    extra: AnyFile,
) -> str:
    """Report the size of three files declared with three different filters.

    Extensions are declared in lowercase and matched case insensitively, so
    a picture named IMAGE.PNG is accepted. A compound extension such as
    ".tar.gz" matches the whole tail, while an empty tuple accepts any name,
    even one without a suffix.
    """
    sizes = [
        f"{Path(path).suffix or 'no suffix'}: "
        f"{Path(path).stat().st_size} bytes"
        for path in (picture, bundle, extra)
    ]

    return " | ".join(sizes)


if __name__ == "__main__":
    run(describe_uploads, title="File extensions")
