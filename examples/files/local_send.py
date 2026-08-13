"""Files are stored on arrival: receiving them takes no code at all."""

from typing import Annotated

from func_to_web import FileHint, Label, Min, run

AnyFile = Annotated[str, FileHint()]

Dropped = Annotated[list[AnyFile], Min(1), Label("Files to send")]


def send(files: Dropped) -> str:
    """Receive any number of files sent to this machine.

    The upload channel stores every file before the function is called, so
    each item is the local path of a file that is already on disk: there is
    nothing left to save. That is why a function that accepts files and does
    nothing else is already a working local file drop, and why the body only
    reports what arrived.
    """
    return f"{len(files)} file(s) received"


if __name__ == "__main__":
    run(send, title="LocalSend")
