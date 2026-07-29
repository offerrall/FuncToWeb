import json
from dataclasses import dataclass
from datetime import date, time
from enum import Enum
from typing import Annotated

import pytest

from func_to_web import Min

CASES = [
    "page",
    "assets",
    "read_scalars",
    "read_optional",
    "read_union",
    "read_list",
    "read_nested",
    "invalid",
    "hidden",
    "prefill",
    "submit",
    "rerun",
]


class Priority(Enum):
    LOW = "low"
    HIGH = "high"


@dataclass
class Where:
    street: Annotated[str, Min(3)] = "Main"
    city: str = "Madrid"


def echo(
    where: Where,
    tags: list[str],
    title: Annotated[str, Min(3)] = "abc",
    count: int = 1,
    ratio: float = 0.5,
    when: date = date(2026, 8, 1),
    at: time = time(9, 30),
    flag: bool = False,
    priority: Priority = Priority.LOW,
    nickname: str | None = None,
    who: str | int = 0,
    token: str = "secret",
) -> str:
    """Echoes everything it receives."""
    return json.dumps(
        {
            "where": [where.street, where.city],
            "tags": tags,
            "title": title,
            "count": count,
            "ratio": ratio,
            "when": when.isoformat(),
            "at": at.isoformat(),
            "flag": flag,
            "priority": priority.name,
            "nickname": nickname,
            "who": who,
            "token": token,
        },
        sort_keys=True,
    )


@pytest.mark.browser
@pytest.mark.slow
@pytest.mark.parametrize("case", CASES)
def test_the_served_form_behaves_in_a_real_browser(verify, app_factory, case):
    verdict, log = verify(app_factory(echo), "form.html", case)

    assert verdict == "PASS", log
