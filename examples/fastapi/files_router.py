"""A mounted space with a file field and a maximum upload size.

max_upload_bytes is the ceiling of the /upload endpoint of this application, per
file and per request: anything bigger is answered with 413 and nothing is
written to disk. The lifetime of what gets stored is the responsibility of
the host application. Serve it as a script or point uvicorn at the module:
uvicorn examples.fastapi.files_router:app
"""

from typing import Annotated

import uvicorn
from fastapi import FastAPI

from func_to_web import FileHint, app_of

MAX_UPLOAD_BYTES = 256 * 1024

TextFile = Annotated[str, FileHint(extensions=(".txt", ".md", ".csv"))]


def count_lines(document: TextFile) -> str:
    """Count the lines of an uploaded text document."""
    with open(document, encoding="utf-8", errors="replace") as file:
        total = sum(1 for _ in file)

    return f"{total} line(s)"


app = FastAPI()

app.mount("/documents", app_of(
    [count_lines],
    title="Documents",
    max_upload_bytes=MAX_UPLOAD_BYTES,
))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
