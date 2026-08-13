"""Accepted extensions: the tuple declared by FileHint is the filter."""

from pathlib import Path
from typing import Annotated

from func_to_web import FileHint, Label, run

ImageFile = Annotated[
    str,
    FileHint(extensions=(".png", ".jpg", ".jpeg")),
    Label("Picture"),
]

ArchiveFile = Annotated[
    str,
    FileHint(extensions=(".tar.gz",)),
    Label("Compressed bundle"),
]

AnyFile = Annotated[str, FileHint(), Label("Anything else")]


def describe_uploads(
    picture: ImageFile,
    bundle: ArchiveFile,
    extra: AnyFile,
) -> str:
    """Report the size of three files declared with three different filters.

    Extensions are declared in lowercase and matched case insensitively, so
    a picture named IMAGE.PNG is accepted. A compound extension such as
    ".tar.gz" matches the whole tail, while an empty tuple accepts any name,
    even one without a suffix. What is compared is always the name, never
    the content: the browser filters what can be picked, and the extension
    of the path is checked once more when the arguments are built, so a
    handwritten call cannot smuggle in a type the field does not accept.
    """
    sizes = [
        f"{Path(path).suffix or 'no suffix'}: "
        f"{Path(path).stat().st_size} bytes"
        for path in (picture, bundle, extra)
    ]

    return " | ".join(sizes)


if __name__ == "__main__":
    run(describe_uploads, title="File extensions")
