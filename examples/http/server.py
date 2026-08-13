"""The space the clients of this folder call over plain HTTP.

Terminal 1: python examples/http/server.py
Terminal 2: python examples/http/invoke_client.py

Every route is relative, so app_with_prefix("/tools") serves the same space
under /tools/greet/invoke without touching a single function.
"""

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI

from func_to_web import Choices, FileHint, Max, Min, app_of, run

TextFile = Annotated[str, FileHint(extensions=(".txt", ".md"))]


def greet(name: str = "world") -> str:
    """Return a greeting: the success case of /invoke."""
    return f"hello {name}"


def book(guests: Annotated[int, Min(1), Max(4)] = 2) -> str:
    """Refuse a party outside the bounds before the body runs."""
    return f"table booked for {guests}"


def divide(numerator: float = 1.0, denominator: float = 0.0) -> str:
    """Raise ZeroDivisionError when the denominator is zero."""
    return f"{numerator / denominator}"


def countdown(steps: Annotated[int, Min(1), Max(10)] = 3) -> str:
    """Print one line per step so the stream carries print events."""
    for index in reversed(range(1, steps + 1)):
        print(f"{index}...")

    return "liftoff"


def measure(
    document: TextFile,
    unit: Annotated[str, Choices(values=("lines", "words"))] = "lines",
) -> str:
    """Measure an uploaded document, reachable by its stored reference."""
    content = Path(document).read_text(encoding="utf-8")
    counted = content.splitlines() if unit == "lines" else content.split()

    return f"{len(counted)} {unit}"


FUNCTIONS = [greet, book, divide, countdown, measure]

TITLE = "HTTP demo"


def app_with_prefix(prefix: str) -> FastAPI:
    """Build an application serving the same space under a mount prefix."""
    app = FastAPI()
    app.mount(prefix, app_of(FUNCTIONS, title=TITLE))

    return app


if __name__ == "__main__":
    run(FUNCTIONS, title=TITLE)
