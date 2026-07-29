"""Call /invoke with the standard library: success, 422 and 500.

Terminal 1: python examples/http/server.py
Terminal 2: python examples/http/invoke_client.py

curl -s -X POST http://127.0.0.1:8000/greet/invoke \
     -H "Content-Type: application/json" -d "{\"name\": \"ada\"}"
"""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8000"

PREFIX = ""

CASES = (
    ("greet", {"name": "ada"}),
    ("book", {"guests": 9}),
    ("divide", {"numerator": 1.0, "denominator": 0.0}),
    ("greet", {"name": "ada", "zzz": 1}),
)


def invoke(slug: str, payload: dict) -> tuple[int, dict]:
    """POST a JSON body to {slug}/invoke and return status and envelope."""
    request = Request(
        f"{BASE}{PREFIX}/{slug}/invoke",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def contract() -> str:
    """GET the plain text contract of the whole space."""
    with urlopen(f"{BASE}{PREFIX}/doc") as response:
        return response.read().decode("utf-8")


def main() -> None:
    """Print the contract header and one line per call."""
    for line in contract().splitlines()[:6]:
        print(line)

    print()

    for slug, payload in CASES:
        status, envelope = invoke(slug, payload)

        print(status, json.dumps(envelope, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except URLError as error:
        raise SystemExit(f"no server at {BASE}: {error.reason}") from None
