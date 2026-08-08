from dataclasses import dataclass
from datetime import date
from typing import Annotated, Literal

import pytest

from func_to_web import Description, Label, Max, Min

CASES = [
    "tall",
    "uncut",
    "limit",
    "configured",
    "relative",
    "bounded",
    "sheet",
]


def report(month: date = date(2026, 8, 1)) -> str:
    """One field."""
    return "ok"


def divide(a: float = 10.0, b: float = 2.0) -> float:
    """Two fields."""
    return a / b


@dataclass
class Task:
    title: Annotated[str, Min(1), Max(80), Label("Title")]
    priority: Literal["low", "normal", "high"] = "normal"
    done: bool = False


def create_task(task: Task, note: str = "",
                due: date = date(2026, 8, 1)) -> str:
    """A nested dataclass and two more fields."""
    return "ok"


def many(
    a: int = 1,
    b: int = 2,
    c: str = "x",
    d: Annotated[str, Description("A description long enough to wrap.")] = "y",
    e: bool = False,
    f: date = date(2026, 8, 1),
    g: Annotated[int, Min(0), Max(10)] = 5,
    h: str = "z",
) -> str:
    """Eight fields: the one that used to be cut off at 760px."""
    return "ok"


SPACE = [report, divide, create_task, many]


# Every size here is relative to the window, so the window is stated instead
# of inherited: headless Chrome opens a small one by default, and 90% of a
# small window says nothing about whether a form fits. This is a common
# laptop.
WINDOW = ("--window-size=1280,1080",)


@pytest.mark.browser
@pytest.mark.slow
@pytest.mark.parametrize("case", CASES)
def test_a_modal_is_sized_by_the_window_in_a_real_browser(verify, app_factory,
                                                           case):
    verdict, log = verify(app_factory(SPACE), "modal.html", case,
                          flags=WINDOW)

    assert verdict == "PASS", log
