import time
from typing import Annotated

import pytest

from func_to_web import Max, Min

CASES = [
    "running",
    "progressive",
    "final",
    "kept",
    "blocked",
    "unicode",
    "failing",
    "bounded",
    "trimmed",
]


def narrate(steps: Annotated[int, Min(1), Max(6)] = 4) -> str:
    """Prints as it works."""
    for index in range(steps):
        print(f"step {index}")
        time.sleep(0.25)

    return "narrated"


def narrate_unicode(seed: int = 1) -> str:
    """Prints beyond ASCII."""
    print("acción · 漢字 · 🎉")
    time.sleep(0.25)
    print("línea 2")
    time.sleep(0.25)

    return "hecho ✓"


def narrate_then_fail(seed: int = 1) -> str:
    """Prints and then fails."""
    print("before the fall")
    time.sleep(0.25)

    raise RuntimeError("it broke")


def narrate_at_length(lines: Annotated[int, Min(1), Max(400)] = 300) -> str:
    """Prints far more than fits on a screen."""
    for index in range(lines):
        print(f"line {index}")

    return "narrated at length"


def narrate_past_the_buffer(seed: int = 1) -> str:
    """Prints more than the page keeps."""
    for index in range(6000):
        print(f"line {index}")

    return "narrated past the buffer"


SPACE = [narrate, narrate_unicode, narrate_then_fail, narrate_at_length,
         narrate_past_the_buffer]


@pytest.mark.browser
@pytest.mark.slow
@pytest.mark.parametrize("case", CASES)
def test_streaming_reaches_the_page_as_it_happens(verify, app_factory, case):
    verdict, log = verify(app_factory(SPACE), "streaming.html", case)

    assert verdict == "PASS", log
