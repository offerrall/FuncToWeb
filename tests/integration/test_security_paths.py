import json
import os
from typing import Annotated
from urllib.parse import urljoin

import pytest
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

from func_to_web import Download, IsPathFile, OpenForm, WebFunction, router_of
from func_to_web.models.function import SLUG_PATTERN
from func_to_web.models.functions import space_of
from func_to_web.templates.index import index_of

TxtFile = Annotated[str, IsPathFile(extensions=(".txt",))]

INJECTION = "<script>alert(1)</script>"

NULL_BYTE = "a\x00b"

LONG_NAME = "a" * 4000

MALICIOUS = (
    "..",
    "../",
    "..\\",
    "%2e%2e",
    "%252e%252e",
    "/",
    "\\",
    "C:\\",
    "C:\\Windows\\win.ini",
    "file://",
    "file:///etc/passwd",
    "NUL",
    "\u2024\u2024",
    "\uff0e\uff0e",
    "\u2215etc\u2215passwd",
    "....//",
    "....\\\\",
    "...",
    ".",
    "../../pyproject.toml",
    "..\\..\\pyproject.toml",
    "/etc/passwd",
    INJECTION,
    NULL_BYTE,
    LONG_NAME,
)

PATH_VECTORS = tuple(
    value for value in MALICIOUS if "\x00" not in value
) + (
    "%00",
    "a%00b",
    "..%2f..%2fpyproject.toml",
    "..%5c..%5cpyproject.toml",
    "%2e%2e%2fpyproject.toml",
    "%252e%252e%252fpyproject.toml",
    "%c0%ae%c0%ae/pyproject.toml",
    "..;/pyproject.toml",
)

RETURN_TRAVERSALS = (
    "../secret.txt",
    "..%2fsecret.txt",
    "..\\secret.txt",
    "..%5csecret.txt",
    "sub/secret.txt",
    "..",
    ".",
)

STACK_TRACE_MARKS = (
    "Traceback (most recent call last)",
    "site-packages",
    'File "',
    "  File ",
)


def loader(document: TxtFile, note: str = "n") -> str:
    """Loads a document."""
    return note


def stamped(seed: int = 1) -> Annotated[bytes, Download("stamp.txt")]:
    """Produces a file."""
    return b"stamp"


def plain(value: str = "v") -> str:
    """Echoes a value."""
    return value


def downloader_named(filename):
    def produced(seed: int = 1) -> Annotated[bytes, Download(filename)]:
        """Produces a named file."""
        return b"payload"

    return produced


def opener_returning(value):
    def opened(seed: int = 1) -> Annotated[dict, OpenForm(loader,
                                                          hidden=("note",))]:
        """Opens the loader form."""
        return {"note": value}

    return opened


def contains_stack_trace(text):
    return any(mark in text for mark in STACK_TRACE_MARKS)


def is_html(response):
    return response.headers.get("content-type", "").startswith("text/html")


def tree_of(root):
    return {path for path in root.rglob("*")}


@pytest.fixture
def tolerant_factory(app_factory):
    clients = []

    def make(fns, prefix="", **options):
        client = TestClient(app_factory(fns, prefix=prefix, **options),
                            raise_server_exceptions=False)
        clients.append(client)
        return client

    yield make

    for client in clients:
        client.close()


@pytest.fixture
def space_client(tolerant_factory):
    return tolerant_factory([loader, stamped], prefix="/s")


@pytest.fixture
def repo_markers(repo_root):
    return {
        "pyproject.toml": (repo_root / "pyproject.toml").read_bytes()[:60],
        "conftest.py": (
            repo_root / "tests" / "conftest.py"
        ).read_bytes()[:60],
        "router.py": (
            repo_root / "src" / "func_to_web" / "web" / "router.py"
        ).read_bytes()[:60],
    }


def linked(link, target):
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"cannot create a symlink on this platform: {error}")


def stamp_reference(client):
    stored = client.post("/s/stamped/invoke", json={"seed": 1})

    assert stored.status_code == 200

    return stored.json()["result"]["value"]


def upload_with(client, reference):
    return client.post(
        "/s/upload",
        headers={b"X-File-Reference": reference.encode("utf-8")},
        content=b"payload",
    )


def test_slug_frontier_never_accepts_a_traversable_slug():
    accepted = []

    for value in MALICIOUS:
        try:
            accepted.append(WebFunction(plain, slug=value).slug)
        except (TypeError, ValueError):
            continue

    assert accepted == [LONG_NAME]

    for slug in accepted:
        assert SLUG_PATTERN.fullmatch(slug)
        assert "/" not in slug
        assert "\\" not in slug
        assert "." not in slug


def test_slug_frontier_keeps_the_reserved_names():
    for reserved in ("static", "doc"):
        with pytest.raises(ValueError):
            WebFunction(plain, slug=reserved)


def test_slug_frontier_only_publishes_its_own_path(tolerant_factory):
    web_function = WebFunction(plain, slug=LONG_NAME)
    client = tolerant_factory([web_function], prefix="/s")

    assert client.get(f"/s/{LONG_NAME}/").status_code == 200
    assert client.get("/s/plain/").status_code == 404


@pytest.mark.parametrize("vector", PATH_VECTORS)
def test_static_frontier_refuses_every_malicious_path(
    space_client, repo_markers, vector
):
    for target in ("", "pyproject.toml", "tests/conftest.py"):
        response = space_client.get(f"/s/static/{vector}{target}")

        assert response.status_code == 404
        assert not is_html(response)
        assert not contains_stack_trace(response.text)

        for marker in repo_markers.values():
            assert marker not in response.content


@pytest.mark.parametrize("vector", MALICIOUS)
def test_upload_frontier_never_writes_outside_its_directory(
    space_client, uploads_dir, tmp_path, vector
):
    before = tree_of(tmp_path)

    upload_with(space_client, vector)

    appeared = tree_of(tmp_path) - before

    for path in appeared:
        assert path.parent == uploads_dir
        assert path.is_relative_to(uploads_dir)


@pytest.mark.parametrize("vector", MALICIOUS)
def test_upload_frontier_never_leaks_a_stack_trace(space_client, vector):
    response = upload_with(space_client, vector)

    assert not contains_stack_trace(response.text)
    assert not is_html(response)
    assert INJECTION not in response.text


def test_upload_frontier_refuses_every_separator_and_dot_reference(
    space_client, uploads_dir
):
    refused = (
        "..", "../", "..\\", "/", "\\", "C:\\", "C:\\Windows\\win.ini",
        "file://", "file:///etc/passwd", "....//", "....\\\\", ".",
        "../../pyproject.toml", "..\\..\\pyproject.toml", "/etc/passwd",
        INJECTION,
    )

    for vector in refused:
        response = upload_with(space_client, vector)

        assert response.status_code == 400, vector
        assert not any(uploads_dir.iterdir()), vector


@pytest.mark.parametrize("vector", MALICIOUS)
def test_upload_frontier_never_answers_an_unhandled_server_error(
    space_client, vector
):
    response = upload_with(space_client, vector)

    assert response.status_code in (200, 400, 413), vector


@pytest.mark.parametrize("vector", PATH_VECTORS)
def test_return_frontier_refuses_every_malicious_reference(
    space_client, repo_markers, vector
):
    response = space_client.get(f"/s/returns/{vector}")

    assert response.status_code == 404
    assert not is_html(response)
    assert not contains_stack_trace(response.text)

    for marker in repo_markers.values():
        assert marker not in response.content


def test_return_frontier_serves_only_its_own_directory(
    space_client, returns_dir, tmp_path
):
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    stored = space_client.post("/s/stamped/invoke", json={"seed": 1})
    reference = stored.json()["result"]["value"]

    assert (returns_dir / reference).is_file()
    assert space_client.get(f"/s/returns/{reference}").status_code == 200
    assert space_client.get("/s/returns/../secret.txt").status_code == 404
    assert space_client.get("/s/returns/..%2fsecret.txt").status_code == 404


def test_return_frontier_serves_an_ordinary_stored_file(space_client):
    reference = stamp_reference(space_client)

    response = space_client.get(f"/s/returns/{reference}")

    assert response.status_code == 200
    assert response.content == b"stamp"


def test_return_frontier_answers_404_for_an_unknown_reference(space_client):
    response = space_client.get("/s/returns/deadbeef.report.txt")

    assert response.status_code == 404
    assert not is_html(response)
    assert not contains_stack_trace(response.text)


@pytest.mark.parametrize("vector", RETURN_TRAVERSALS)
def test_return_frontier_refuses_a_traversal_to_a_real_file(
    space_client, returns_dir, tmp_path, vector
):
    (tmp_path / "secret.txt").write_text("secret", encoding="utf-8")
    (returns_dir.parent / "secret.txt").write_text("secret", encoding="utf-8")

    response = space_client.get(f"/s/returns/{vector}")

    assert response.status_code == 404
    assert b"secret" not in response.content
    assert not contains_stack_trace(response.text)


def test_return_frontier_refuses_a_symlink_that_escapes_the_directory(
    space_client, returns_dir, tmp_path
):
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    escaping = f"{'0' * 32}.escape.txt"

    linked(returns_dir / escaping, outside)

    response = space_client.get(f"/s/returns/{escaping}")

    assert response.status_code == 404
    assert b"secret" not in response.content
    assert not contains_stack_trace(response.text)


def test_return_frontier_serves_a_symlink_that_stays_inside_the_directory(
    space_client, returns_dir
):
    reference = stamp_reference(space_client)
    alias = f"{'1' * 32}.alias.txt"

    linked(returns_dir / alias, returns_dir / reference)

    response = space_client.get(f"/s/returns/{alias}")

    assert response.status_code == 200
    assert response.content == b"stamp"


@pytest.mark.parametrize("vector", MALICIOUS)
def test_prefill_frontier_refuses_every_malicious_file_reference(
    space_client, repo_markers, vector
):
    response = space_client.get(
        "/s/loader/", params={"prefill": json.dumps({"document": vector})}
    )

    assert response.status_code == 400
    assert not is_html(response)
    assert not contains_stack_trace(response.text)

    for marker in repo_markers.values():
        assert marker.decode("utf-8", "replace") not in response.text


@pytest.mark.parametrize("vector", MALICIOUS)
def test_prefill_frontier_escapes_every_accepted_text(space_client, vector):
    response = space_client.get(
        "/s/loader/", params={"prefill": json.dumps({"note": vector})}
    )

    assert response.status_code == 200
    assert is_html(response)
    assert "<script>alert" not in response.text
    assert "</script>alert" not in response.text
    assert not contains_stack_trace(response.text)


@pytest.mark.parametrize("vector", MALICIOUS)
def test_prefill_frontier_refuses_a_malformed_query(space_client, vector):
    response = space_client.get("/s/loader/", params={"prefill": vector})

    assert response.status_code == 400
    assert not is_html(response)
    assert not contains_stack_trace(response.text)


@pytest.mark.parametrize("vector", MALICIOUS)
def test_hidden_frontier_answers_without_reflecting_markup(
    space_client, vector
):
    raw = space_client.get("/s/loader/", params={"hidden": vector})

    assert raw.status_code == 400
    assert not is_html(raw)

    listed = space_client.get(
        "/s/loader/", params={"hidden": json.dumps([vector])}
    )

    assert listed.status_code == 200
    assert is_html(listed)
    assert "<script>alert" not in listed.text
    assert not contains_stack_trace(listed.text)


@pytest.mark.parametrize("vector", MALICIOUS)
def test_download_filename_frontier_stays_in_the_returns_directory(
    tolerant_factory, returns_dir, tmp_path, vector
):
    client = tolerant_factory(downloader_named(vector), prefix="/s")
    before = tree_of(tmp_path)

    response = client.post("/s/produced/invoke", json={"seed": 1})

    assert response.status_code in (200, 500)

    body = response.json()

    assert ("result" in body) != ("error" in body)
    assert not contains_stack_trace(response.text)

    for path in tree_of(tmp_path) - before:
        assert path.parent == returns_dir

    if response.status_code != 200:
        return

    reference = body["result"]["value"]

    assert "/" not in reference
    assert "\\" not in reference
    assert (returns_dir / reference).resolve().parent == returns_dir.resolve()
    assert (returns_dir / reference).is_file()


def test_download_filename_frontier_refuses_a_traversing_name(
    tolerant_factory, returns_dir
):
    for vector in ("../evil.txt", "..\\evil.txt", "..", "/", "\\", "."):
        client = tolerant_factory(downloader_named(vector), prefix="/s")
        response = client.post("/s/produced/invoke", json={"seed": 1})

        assert response.status_code == 500, vector
        assert "ReturnContractError" in response.json()["error"], vector
        assert not any(returns_dir.iterdir()), vector


@pytest.mark.parametrize("vector", MALICIOUS)
def test_open_form_href_frontier_stays_relative(tolerant_factory, vector):
    client = tolerant_factory([opener_returning(vector), loader], prefix="/s")
    response = client.post("/s/opened/invoke", json={"seed": 1})

    assert response.status_code == 200

    href = response.json()["result"]["href"]

    assert href.startswith("../loader/?")
    assert not href.lower().startswith(("http:", "https:", "javascript:",
                                        "data:", "file:", "//"))
    assert "\n" not in href
    assert "\r" not in href
    assert "<" not in href
    assert "\\" not in href

    followed = client.get(urljoin("http://testserver/s/opened/", href))

    assert followed.status_code == 200
    assert is_html(followed)
    assert "<script>alert" not in followed.text
    assert not contains_stack_trace(followed.text)


def test_open_form_href_never_targets_a_foreign_path(tolerant_factory):
    client = tolerant_factory([opener_returning("x"), loader], prefix="/s")
    href = client.post(
        "/s/opened/invoke", json={"seed": 1}
    ).json()["result"]["href"]

    resolved = urljoin("http://testserver/s/opened/", href)

    assert resolved.startswith("http://testserver/s/loader/?")


def test_injected_markup_is_escaped_everywhere_it_is_served(tolerant_factory):
    web_function = WebFunction(
        plain,
        name=f"Name {INJECTION}",
        description=f"Desc {INJECTION}",
        slug="injected",
    )
    space = space_of([web_function], f"Title {INJECTION}")

    app = FastAPI()
    app.include_router(router_of(space), prefix="")
    rendered = index_of(space, "")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return rendered

    with TestClient(app) as client:
        pages = [
            client.get("/"),
            client.get("/injected/"),
            client.get("/injected/",
                       params={"prefill": json.dumps({"value": INJECTION})}),
            client.get("/injected/",
                       params={"hidden": json.dumps([INJECTION])}),
        ]

        for response in pages:
            assert response.status_code == 200
            assert is_html(response)
            assert INJECTION not in response.text
            assert "<script>alert" not in response.text
            assert "alert(1)" in response.text or "alert%281%29" in response.text

        assert "&lt;script&gt;" in pages[0].text
        assert "&lt;script&gt;" in pages[1].text
        assert "\\u003cscript>" in pages[2].text
        assert "\\u003cscript>" in pages[3].text


def test_the_whole_attack_matrix_creates_no_file_outside_the_temporary_dirs(
    space_client, tolerant_factory, uploads_dir, returns_dir, tmp_path,
    repo_root
):
    watched = (tmp_path, repo_root / "src", repo_root / "tests")
    before = {root: tree_of(root) for root in watched}
    before_files = {
        repo_root: {path for path in repo_root.iterdir() if path.is_file()}
    }

    for vector in MALICIOUS:
        upload_with(space_client, vector)
        space_client.get("/s/loader/",
                         params={"prefill": json.dumps({"document": vector})})
        space_client.get("/s/loader/",
                         params={"prefill": json.dumps({"note": vector})})
        space_client.get("/s/loader/", params={"hidden": vector})
        space_client.get("/s/loader/",
                         params={"hidden": json.dumps([vector])})
        space_client.post("/s/loader/invoke",
                          json={"document": vector, "note": vector})

    for vector in PATH_VECTORS:
        space_client.get(f"/s/static/{vector}pyproject.toml")
        space_client.get(f"/s/returns/{vector}")

    for vector in MALICIOUS:
        client = tolerant_factory(downloader_named(vector), prefix="/s")
        client.post("/s/produced/invoke", json={"seed": 1})

    for root in watched:
        appeared = tree_of(root) - before[root]

        for path in appeared:
            assert (path.is_relative_to(uploads_dir)
                    or path.is_relative_to(returns_dir)), path

    assert {path for path in repo_root.iterdir()
            if path.is_file()} == before_files[repo_root]
