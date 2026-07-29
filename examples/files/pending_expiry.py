"""pending_ttl is how long an upload nobody used survives before deletion."""

from pathlib import Path
from typing import Annotated

from func_to_web import IsPathFile, Label, run

PENDING_TTL = 60

TextFile = Annotated[
    str,
    IsPathFile(extensions=(".txt", ".md")),
    Label("Document"),
]


def measure_document(document: TextFile) -> str:
    """Report the size of a document that is now stored for good.

    Submitting uploads the bytes and executes right afterwards, and what
    promotes a file is resolving its reference, before the function is even
    called: the path this function receives is already permanent, and this
    TTL will never reach it. What the TTL governs is the other case, bytes
    that reached /upload and never reached an execution —a client that
    uploads ahead of time, a form abandoned after its upload was confirmed—
    which are deleted once they are older than the TTL of this space, either
    by the resolver that walks past them or by the periodic sweep.
    """
    size = Path(document).stat().st_size

    return f"{size} bytes, stored under {Path(document).name}"


if __name__ == "__main__":
    run(measure_document, title="Pending expiry", pending_ttl=PENDING_TTL)
