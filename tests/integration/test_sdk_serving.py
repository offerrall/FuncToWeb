import json
import re
from pathlib import Path
from typing import Annotated

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from func_to_web import Download, IsPathFile, Min, app_of

PREFIX = "/tools"

ASSET = f"{PREFIX}/static/sdk.js"

EXPORTS = re.compile(r"^export (?:async )?(?:function\*? |class )(\w+)",
                     re.MULTILINE)

EXPECTED_EXPORTS = {
    "FuncToWebError", "fileReference", "outputsOf", "call", "events",
    "callStream", "upload", "doc", "downloadUrl", "formUrl", "pageUrl",
    "embed", "openModal", "listen",
}


def add(a: int, b: Annotated[int, Min(0)] = 2) -> int:
    """Add two numbers."""
    print("adding")
    return a + b


def divide(a: float, b: float) -> float:
    """Divide the first number by the second one."""
    return a / b


def count_lines(source: Annotated[str, IsPathFile(extensions=(".csv",))]) -> str:
    """Count the lines of a file."""
    return str(len(Path(source).read_text(encoding="utf-8").splitlines()))


def report() -> Annotated[Path, Download()]:
    """Build a report."""
    path = Path("report.csv")
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    return path


SPACE = [add, divide, count_lines, report]

TITLE = "Internal tools"


@pytest.fixture
def hosted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    app = FastAPI()
    app.mount(PREFIX, app_of(SPACE, title=TITLE))

    with TestClient(app) as client:
        yield client


@pytest.fixture
def module(hosted):
    return hosted.get(ASSET).text


def test_the_space_serves_the_helpers_as_javascript(hosted):
    response = hosted.get(ASSET)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/javascript")


def test_the_helpers_are_the_ones_the_page_documents(module):
    assert set(EXPORTS.findall(module)) == EXPECTED_EXPORTS


def test_the_helpers_carry_no_trace_of_the_space(module):
    assert TITLE not in module
    assert "add" not in EXPORTS.findall(module)


def test_the_route_call_builds_answers_on_every_slug(hosted):
    for slug in ("add", "divide", "count_lines", "report"):
        assert hosted.get(f"{PREFIX}/{slug}/").status_code == 200


def test_the_route_call_builds_returns_the_envelope(hosted):
    response = hosted.post(f"{PREFIX}/add/invoke", json={"a": 1, "b": 2})

    assert response.json() == {"result": {"type": "text", "value": "3"}}


def test_the_arguments_the_helpers_do_not_check_the_server_refuses(hosted):
    missing = hosted.post(f"{PREFIX}/add/invoke", json={})
    unexpected = hosted.post(f"{PREFIX}/add/invoke", json={"a": 1, "z": 2})

    assert missing.json() == {"error": "SchemaTypeError: missing argument(s): a"}
    assert unexpected.json() == {
        "error": "SchemaTypeError: unexpected argument(s): z"
    }


def test_the_route_upload_builds_accepts_a_minted_reference(hosted):
    reference = "data-0123456789abcdef.csv"

    stored = hosted.post(
        f"{PREFIX}/upload",
        content=b"a,b\n1,2\n3,4\n",
        headers={
            "Content-Type": "application/octet-stream",
            "X-File-Reference": reference,
        },
    )

    assert stored.json() == {"uploaded": True}

    used = hosted.post(f"{PREFIX}/count_lines/invoke", json={"source": reference})

    assert used.json() == {"result": {"type": "text", "value": "3"}}


def test_the_url_download_url_builds_serves_the_file(hosted):
    output = hosted.post(f"{PREFIX}/report/invoke", json={}).json()["result"]
    fetched = hosted.get(f"{PREFIX}/returns/{output['value']}")

    assert fetched.status_code == 200
    assert fetched.text.startswith("a,b")


def test_the_url_page_url_builds_opens_prefilled(hosted):
    query = {"prefill": json.dumps({"a": 9}), "hidden": json.dumps(["a"])}
    response = hosted.get(f"{PREFIX}/add/", params=query)

    assert response.status_code == 200
    assert '"default": 9' in response.text


def test_the_route_doc_builds_publishes_the_contract(hosted):
    response = hosted.get(f"{PREFIX}/doc")

    assert response.status_code == 200
    assert "--- /add ---" in response.text


def test_the_helpers_do_not_change_between_requests(hosted):
    assert hosted.get(ASSET).text == hosted.get(ASSET).text
