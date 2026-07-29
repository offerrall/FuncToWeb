"""Send the bytes once to /upload, then reuse the reference twice.

Terminal 1: python examples/http/server.py
Terminal 2: python examples/http/upload_client.py

invoke() is imported from the client next to it, which works from any working
directory because Python puts the folder of the script first on sys.path; run
as a module (-m) it would not, and there is no need to.

curl -X POST http://127.0.0.1:8000/upload \
     -H "X-File-Reference: notes-<uuid>.txt" --data-binary @notes.txt
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from invoke_client import invoke

BASE = "http://127.0.0.1:8000"

PREFIX = ""

SAMPLE = "alpha beta\ngamma delta\nepsilon\n"


def upload(path: Path) -> str:
    """Send the bytes of a file and return the minted reference."""
    reference = f"{path.stem}-{uuid4().hex}{path.suffix}"

    request = Request(
        f"{BASE}{PREFIX}/upload",
        data=path.read_bytes(),
        headers={
            "X-File-Reference": reference,
            "Content-Type": "application/octet-stream",
        },
        method="POST",
    )

    with urlopen(request) as response:
        json.load(response)

    return reference


def main() -> None:
    """Upload a temporary document and measure it twice."""
    with TemporaryDirectory() as folder:
        path = Path(folder) / "notes.txt"
        path.write_text(SAMPLE, encoding="utf-8")

        reference = upload(path)

    print(reference)

    for payload in ({"document": reference, "unit": "lines"},
                    {"document": reference, "unit": "words"},
                    {"document": "nope-0000.txt"}):
        status, envelope = invoke("measure", payload)

        print(status, json.dumps(envelope, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        raise SystemExit(f"upload refused: {error.code}") from None
    except URLError as error:
        raise SystemExit(f"no server at {BASE}: {error.reason}") from None
