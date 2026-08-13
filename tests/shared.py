import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from func_to_web import FileHint, Min


def warm_uvicorn() -> None:
    # uvicorn.Config.load() imports its protocol backends lazily, from inside
    # the thread live_server starts. websockets.legacy raises a
    # DeprecationWarning on import, and filterwarnings=["error"] turns it into
    # an exception there, so the server never reaches started and every
    # browser test dies on a fifteen second timeout. Importing the backends
    # once here, with warnings ignored, leaves them in sys.modules and lets
    # live_server work as it was meant to.
    import uvicorn
    from fastapi import FastAPI

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        try:
            uvicorn.Config(FastAPI(), host="127.0.0.1", port=0).load()
        except Exception:
            pass

def carries(text: str, path) -> bool:
    # A path reaches the client in three renderings, and a plain `in` catches
    # only the first: JSON doubles a Windows separator, and the core's !r
    # messages double it again. A guard that looks for str(path) alone passes
    # with the path in plain sight.
    import json

    rendered = str(path)

    return any(form in text
               for form in (rendered,
                            json.dumps(rendered)[1:-1],
                            repr(rendered)[1:-1]))


TxtFile = Annotated[str, FileHint(extensions=(".txt",))]
AnyFile = Annotated[str, FileHint()]


class Priority(Enum):
    LOW = "low"
    HIGH = "high"


@dataclass
class Address:
    street: Annotated[str, Min(3)]
    city: str = "Madrid"


@dataclass
class Attachment:
    document: TxtFile
    tag: str = "t"
