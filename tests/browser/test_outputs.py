import time
from typing import Annotated

import pandas
import pytest
from fastapi import FastAPI
from fastapi.responses import Response
from PIL import Image

from func_to_web import Download, OpenForm, app_of

CASES = [
    "text",
    "escaping",
    "error",
    "running",
    "stdout",
    "table",
    "image",
    "download",
    "form",
    "several",
    "icons",
    "accessibility",
]

HOSTILE = '<img src=x onerror="document.title=\'pwned\'">'

STUB = (
    "event: start\n"
    "data: {}\n\n"
    "event: result\n"
    'data: {"result": {"type": "mystery", "value": "?"}}\n\n'
)


def as_text(value: str = "plain answer") -> str:
    """Answers with text."""
    return value


def as_hostile(seed: int = 1) -> str:
    """Answers with markup inside its text."""
    return HOSTILE * seed


def as_error(seed: int = 1) -> str:
    """Always fails."""
    raise RuntimeError("something broke")


def as_slow(seed: int = 1) -> str:
    """Takes a moment."""
    time.sleep(0.4)
    return "late answer"


def as_printing(lines: int = 3) -> str:
    """Prints before answering."""
    for index in range(lines):
        print(f"line {index}")
    return "printed answer"


def as_table(seed: int = 1) -> pandas.DataFrame:
    """Answers with a table."""
    return pandas.DataFrame({"name": ["ada", "alan"], "score": [10, 20]})


def as_image(seed: int = 1) -> Image.Image:
    """Answers with an image."""
    return Image.new("RGB", (8, 4), (200, 30, 30))


def as_download(seed: int = 1) -> Annotated[bytes, Download("out.txt")]:
    """Answers with a file."""
    return b"payload"


def as_several(seed: int = 1) -> list[str]:
    """Answers with several outputs."""
    return ["first answer", "second answer"]


def edit(product_id: int, name: str = "x") -> str:
    """Edits a product."""
    return name


def as_form(product_id: int = 7) -> Annotated[
    dict, OpenForm(edit, hidden=("product_id",))
]:
    """Answers by opening another form."""
    return {"product_id": product_id, "name": "chosen"}


def as_broken(seed: int = 1) -> str:
    """Never answers for real."""
    return "unreachable"


SPACE = [as_text, as_hostile, as_error, as_slow, as_printing, as_table,
         as_image, as_download, as_several, as_form, edit]


@pytest.mark.browser
@pytest.mark.slow
@pytest.mark.parametrize("case", CASES)
def test_outputs_render_in_a_real_browser(verify, app_factory, case):
    verdict, log = verify(app_factory(SPACE), "outputs.html", case)

    assert verdict == "PASS", log


@pytest.mark.browser
@pytest.mark.slow
def test_an_output_the_client_cannot_render_is_refused(verify):
    app = FastAPI()

    @app.post("/tools/as_broken/invoke-stream")
    async def stub() -> Response:
        return Response(STUB, media_type="text/event-stream")

    app.mount("/tools", app_of(as_broken))

    verdict, log = verify(app, "outputs.html", "invalid", prefix="/tools")

    assert verdict == "PASS", log
