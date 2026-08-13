from pathlib import Path
from typing import Annotated

import pytest

from func_to_web import Download, FileHint

CASES = ["page", "assets", "submit", "upload", "download", "outside"]

PREFIX = "/tools/anidado"

TxtFile = Annotated[str, FileHint(extensions=(".txt",))]


def add(a: int, b: int = 2) -> int:
    """Adds two numbers."""
    return a + b


def take_one(document: TxtFile) -> str:
    """Reads one file."""
    return Path(document).read_text(encoding="utf-8")


def pack(seed: int = 3) -> Annotated[bytes, Download("out.txt")]:
    """Packs a file."""
    return b"x" * seed


SPACE = [add, take_one, pack]


@pytest.mark.browser
@pytest.mark.slow
@pytest.mark.parametrize("case", CASES)
def test_a_space_under_a_prefix_works_in_a_real_browser(verify, app_factory,
                                                        case):
    verdict, log = verify(app_factory(SPACE, prefix=PREFIX), "prefix.html",
                          case, prefix=PREFIX)

    assert verdict == "PASS", log
