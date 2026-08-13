from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import pytest

from func_to_web import FileHint

CASES = [
    "valid",
    "min_size",
    "max_size",
    "size_boundary",
    "extension",
    "multiple",
    "nested",
    "rows",
    "prefilled",
    "replace",
    "upload_flow",
    "refused_never_uploads",
]

STORED = "stored.txt"
STORED_CONTENT = b"stored bytes"

TxtFile = Annotated[str, FileHint(extensions=(".txt",))]
BoundedFile = Annotated[
    str, FileHint(extensions=(".txt",), min_size=50, max_size=120)
]


@dataclass
class Attachment:
    document: TxtFile
    tag: str = "t"


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def take_one(document: TxtFile) -> str:
    """Reads one file."""
    return read_text(document)


def take_many(documents: list[TxtFile]) -> str:
    """Reads several files."""
    return "|".join(read_text(item) for item in documents)


def take_bounded(document: BoundedFile) -> str:
    """Reads a file of a bounded size."""
    return read_text(document)


def take_nested(item: Attachment) -> str:
    """Reads a file inside a dataclass."""
    return f"{item.tag}:{read_text(item.document)}"


def take_rows(rows: list[Attachment]) -> str:
    """Reads a file per row."""
    return "|".join(f"{row.tag}:{read_text(row.document)}" for row in rows)


SPACE = [take_one, take_many, take_bounded, take_nested, take_rows]


@pytest.mark.browser
@pytest.mark.slow
@pytest.mark.parametrize("case", CASES)
def test_file_fields_behave_in_a_real_browser(verify, app_factory,
                                              stored_file, case):
    stored_file(STORED, data=STORED_CONTENT)

    verdict, log = verify(app_factory(SPACE), "files.html", case,
                          query={"stored": STORED})

    assert verdict == "PASS", log
