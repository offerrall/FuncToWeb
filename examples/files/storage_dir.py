"""uploads_dir says where the uploaded files are kept, argument first."""

from pathlib import Path
from typing import Annotated

from func_to_web import IsPathFile, Label, run

STORAGE = Path(__file__).resolve().parent / "storage"

TextFile = Annotated[
    str,
    IsPathFile(extensions=(".txt", ".md")),
    Label("Document"),
]


def store_document(document: TextFile) -> str:
    """Report where the received document was stored.

    Three sources name that directory, and they are read in this order: the
    uploads_dir argument, the FUNCTOWEB_UPLOADS_DIR variable and the user's
    data directory. Whichever wins is made absolute and created when the
    router is built, so a location this process cannot write to is a failure
    of the build and never of the first request. It is settled once per
    process, not once per router: the first space with file fields decides
    for every space mounted beside it. This one derives its folder from
    __file__ because a relative path would be resolved against the working
    directory of the process, which is not where the code lives.
    """
    path = Path(document)

    return f"{path.name} stored in {path.parent}"


if __name__ == "__main__":
    run(store_document, title="Storage directory", uploads_dir=STORAGE)
