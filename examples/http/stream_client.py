"""Consume /invoke-stream as SSE with the standard library.

Terminal 1: python examples/http/server.py
Terminal 2: python examples/http/stream_client.py

curl -N -X POST http://127.0.0.1:8000/countdown/invoke-stream \
     -H "Content-Type: application/json" -d "{\"steps\": 3}"
"""

import json
from collections.abc import Iterator
from urllib.error import URLError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8000"

PREFIX = ""


def events(slug: str, payload: dict) -> Iterator[tuple[str, dict]]:
    """Yield every (name, data) event sent by {slug}/invoke-stream."""
    request = Request(
        f"{BASE}{PREFIX}/{slug}/invoke-stream",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    name = ""

    with urlopen(request) as response:
        for raw in response:
            line = raw.decode("utf-8").rstrip("\r\n")

            if line.startswith("event: "):
                name = line[len("event: "):]
            elif line.startswith("data: "):
                yield name, json.loads(line[len("data: "):])


def main() -> None:
    """Show what the function prints, then its final envelope."""
    for name, data in events("countdown", {"steps": 3}):
        if name == "print":
            print(data["text"], end="", flush=True)
        elif name == "result":
            print(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except URLError as error:
        raise SystemExit(f"no server at {BASE}: {error.reason}") from None
