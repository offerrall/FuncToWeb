from pathlib import Path
from typing import Annotated
from urllib.parse import urljoin

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from func_to_web import (
    Download,
    FileHint,
    OpenForm,
    WebFunction,
    app_of,
)

TxtFile = Annotated[str, FileHint(extensions=(".txt",))]

PREFIXES = ["", "/tools", "/a/b/c"]


def read(document: TxtFile) -> str:
    """Reads a file."""
    return Path(document).read_text(encoding="utf-8")


def pack(seed: int = 3) -> Annotated[bytes, Download("out.txt")]:
    """Packs a file."""
    return b"x" * seed


def add(a: int, b: int = 2) -> int:
    """Adds two numbers."""
    return a + b


def times_ten(a: int) -> int:
    """Multiplies by ten."""
    return a * 10


def edit_product(product_id: int, name: str = "x") -> str:
    """Edits a product."""
    return name


def select_product(product_id: int = 1) -> Annotated[
    dict,
    OpenForm(edit_product, hidden=("product_id",)),
]:
    """Selects a product."""
    return {"product_id": product_id, "name": "chosen"}


SPACE = [add, read, pack, select_product, edit_product]


@pytest.fixture(params=PREFIXES)
def prefix(request):
    return request.param


@pytest.fixture
def mounted(client_factory, prefix):
    return client_factory(SPACE, prefix=prefix), prefix


def test_the_page_is_served_under_any_prefix(mounted):
    client, prefix = mounted

    response = client.get(f"{prefix}/add/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_every_function_of_the_space_is_served_under_any_prefix(mounted):
    client, prefix = mounted

    for slug in ("add", "read", "pack", "select_product", "edit_product"):
        assert client.get(f"{prefix}/{slug}/").status_code == 200


def test_a_page_without_its_trailing_slash_redirects_inside_the_prefix(
    mounted,
):
    client, prefix = mounted

    response = client.get(f"{prefix}/add", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].endswith(f"{prefix}/add/")


def test_doc_is_served_under_any_prefix(mounted):
    client, prefix = mounted

    response = client.get(f"{prefix}/doc")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "add" in response.text


def test_page_css_is_served_under_any_prefix(mounted):
    client, prefix = mounted

    response = client.get(f"{prefix}/static/page.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")


def test_an_icon_in_a_subdirectory_is_served_under_any_prefix(mounted):
    client, prefix = mounted

    response = client.get(f"{prefix}/static/icons/copy.svg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"


def test_widgets_css_from_pytypehintweb_is_served_under_any_prefix(mounted):
    client, prefix = mounted

    response = client.get(f"{prefix}/static/widgets.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert "--pth-" in response.text


def test_page_js_is_served_under_any_prefix(mounted):
    client, prefix = mounted

    response = client.get(f"{prefix}/static/page.js")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/javascript")


def test_a_missing_static_asset_is_404_under_any_prefix(mounted):
    client, prefix = mounted

    assert client.get(f"{prefix}/static/nope.css").status_code == 404


def test_upload_is_served_under_any_prefix(mounted):
    client, prefix = mounted

    response = client.post(f"{prefix}/upload", content=b"hello",
                           headers={"X-File-Reference": "a.txt"})

    assert response.status_code == 200
    assert response.json() == {"uploaded": True}


def test_an_uploaded_file_reaches_invoke_under_any_prefix(mounted):
    client, prefix = mounted

    client.post(f"{prefix}/upload", content=b"hello",
                headers={"X-File-Reference": "a.txt"})
    response = client.post(f"{prefix}/read/invoke", json={"document": "a.txt"})

    assert response.json() == {"result": {"type": "text", "value": "hello"}}


def test_returns_is_served_under_any_prefix(mounted):
    client, prefix = mounted

    reference = client.post(f"{prefix}/pack/invoke",
                            json={"seed": 4}).json()["result"]["value"]
    response = client.get(f"{prefix}/returns/{reference}")

    assert response.status_code == 200
    assert response.content == b"xxxx"


def test_the_returns_link_of_an_output_resolves_under_any_prefix(mounted):
    client, prefix = mounted

    result = client.post(f"{prefix}/pack/invoke",
                         json={"seed": 2}).json()["result"]
    target = urljoin(f"{prefix}/pack/", f"../returns/{result['value']}")

    assert client.get(target).content == b"xx"


def test_invoke_is_served_under_any_prefix(mounted):
    client, prefix = mounted

    response = client.post(f"{prefix}/add/invoke", json={"a": 1, "b": 2})

    assert response.status_code == 200
    assert response.json() == {"result": {"type": "text", "value": "3"}}


def test_invoke_stream_is_served_under_any_prefix(mounted, sse):
    client, prefix = mounted

    response = client.post(f"{prefix}/add/invoke-stream",
                           json={"a": 1, "b": 2})
    events = sse(response.text)

    assert response.headers["content-type"].startswith("text/event-stream")
    assert events[0][0] == "start"
    assert events[-1] == ("result", {"result": {"type": "text",
                                                "value": "3"}})


def test_prefill_is_served_under_any_prefix(mounted, plan_of_page):
    client, prefix = mounted

    html = client.get(f"{prefix}/add/", params={"prefill": '{"a": 41}'}).text
    fields = {field["name"]: field["default"]
              for field in plan_of_page(html)["fields"]}

    assert fields["a"] == 41


def test_the_served_html_carries_no_absolute_paths(mounted):
    client, prefix = mounted

    html = client.get(f"{prefix}/add/").text

    assert '"/static/' not in html
    assert "http://" not in html
    assert "127.0.0.1" not in html


def test_the_served_html_links_its_assets_relatively(mounted):
    client, prefix = mounted

    html = client.get(f"{prefix}/add/").text

    assert '"../static/widgets.css"' in html
    assert '"../static/page.css"' in html
    assert '"../static/page.js"' in html


def test_the_open_form_href_is_relative_under_any_prefix(mounted):
    client, prefix = mounted

    href = client.post(f"{prefix}/select_product/invoke",
                       json={"product_id": 7}).json()["result"]["href"]

    assert href.startswith("../edit_product/?")


def test_the_open_form_href_resolves_under_any_prefix(mounted):
    client, prefix = mounted

    href = client.post(f"{prefix}/select_product/invoke",
                       json={"product_id": 7}).json()["result"]["href"]
    target = urljoin(f"{prefix}/select_product/", href)

    assert client.get(target).status_code == 200


def test_the_open_form_target_opens_prefilled_under_any_prefix(
    mounted, plan_of_page,
):
    client, prefix = mounted

    href = client.post(f"{prefix}/select_product/invoke",
                       json={"product_id": 7}).json()["result"]["href"]
    html = client.get(urljoin(f"{prefix}/select_product/", href)).text
    fields = {field["name"]: field["default"]
              for field in plan_of_page(html)["fields"]}

    assert fields == {"product_id": 7, "name": "chosen"}


@pytest.mark.parametrize("mount", ["/tools", "/a/b/c"])
def test_nothing_of_the_space_answers_outside_its_prefix(client_factory,
                                                         mount):
    client = client_factory(SPACE, prefix=mount)

    assert client.get("/add/").status_code == 404
    assert client.get("/doc").status_code == 404
    assert client.get("/static/page.css").status_code == 404


def test_two_prefixes_in_one_application_do_not_collide():
    app = FastAPI()
    app.mount("/a", app_of(add))
    app.mount("/b", app_of(WebFunction(times_ten, name="add", slug="add")))

    with TestClient(app) as client:
        first = client.post("/a/add/invoke", json={"a": 1, "b": 2})
        second = client.post("/b/add/invoke", json={"a": 1})

    assert first.json() == {"result": {"type": "text", "value": "3"}}
    assert second.json() == {"result": {"type": "text", "value": "10"}}


def test_two_prefixes_in_one_application_keep_their_own_pages(html_root):
    app = FastAPI()
    app.mount("/a", app_of(add, theme="light"))
    app.mount("/b", app_of(add, theme="dark"))

    with TestClient(app) as client:
        light = client.get("/a/add/").text
        dark = client.get("/b/add/").text

    assert html_root(light) == '<html data-pth-theme="light">'
    assert html_root(dark) == '<html data-pth-theme="dark">'


def test_two_prefixes_in_one_application_keep_their_own_documents():
    app = FastAPI()
    app.mount("/a", app_of(add, title="First"))
    app.mount("/b", app_of(read, title="Second"))

    with TestClient(app) as client:
        first = client.get("/a/doc").text
        second = client.get("/b/doc").text

    assert "First" in first
    assert "Second" not in first
    assert "Second" in second
    assert "First" not in second


def test_two_prefixes_in_one_application_keep_their_own_upload_limits():
    app = FastAPI()
    app.mount("/a", app_of(read, max_upload_bytes=2))
    app.mount("/b", app_of(read))

    with TestClient(app) as client:
        strict = client.post("/a/upload", content=b"hello",
                             headers={"X-File-Reference": "a.txt"})
        loose = client.post("/b/upload", content=b"hello",
                            headers={"X-File-Reference": "b.txt"})

    assert strict.status_code == 413
    assert loose.status_code == 200
