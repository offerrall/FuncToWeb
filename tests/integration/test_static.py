import re
import shutil
from pathlib import Path
from urllib.parse import urljoin

import pytest

from func_to_web.web import router as router_module

OWN_ASSETS = (
    "page.js",
    "output.js",
    "upload.js",
    "sdk.js",
    "page.css",
    "icons/alert.svg",
    "icons/check.svg",
    "icons/clock.svg",
    "icons/copy.svg",
    "icons/download.svg",
)

WIDGET_ASSETS = (
    "form.js",
    "contract.js",
    "normalize.js",
    "fields.js",
    "inputs.js",
    "defaults.js",
    "iso.js",
    "slider.js",
    "widgets.css",
    "icons/trash.svg",
    "icons/select-arrow-light.svg",
    "icons/select-arrow-dark.svg",
)

ALL_ASSETS = OWN_ASSETS + WIDGET_ASSETS

CRAWLED_ASSETS = tuple(name for name in ALL_ASSETS if name != "sdk.js")

EXPECTED_TYPES = {
    ".js": "text/javascript",
    ".css": "text/css",
    ".svg": "image/svg+xml",
}

REJECTED_PATHS = (
    "unknown.js",
    "icons",
    "",
    "..",
    "../",
    "../router.py",
    "%2e%2e",
    "%2e%2e/router.py",
    "%252e%252e",
    "%252e%252e/router.py",
    "/page.js",
    "//page.js",
    "\\page.js",
    "..\\router.py",
    "C:\\Windows\\win.ini",
    "/etc/passwd",
    "file:///etc/passwd",
    "file://page.js",
)

ESCAPE_VECTORS = (
    "{name}",
    "../{name}",
    "../../{name}",
    "../../../{name}",
    "../../../../{name}",
    "../../../../../{name}",
    "..\\{name}",
    "..\\..\\{name}",
    "..\\..\\..\\..\\{name}",
    "./../../{name}",
    ".%2e/{name}",
    "%2e%2e/{name}",
    "%2e%2e%2f{name}",
    "%2E%2E/{name}",
    "%2e%2e%5c{name}",
    "%252e%252e/{name}",
    "%252e%252e%252f{name}",
    "..%2f..%2f{name}",
    "..%5c..%5c{name}",
    "..%00/{name}",
    "%00../{name}",
    "%c0%ae%c0%ae/{name}",
    "..;/{name}",
    "....//....//{name}",
    "....\\\\....\\\\{name}",
    ".../{name}",
    "icons/../../{name}",
    "icons/..%2f..%2f{name}",
    "static/../../{name}",
    "/{name}",
    "//{name}",
    "\\{name}",
    "~/{name}",
    "file://../{name}",
    "\u2024\u2024/{name}",
    "\uff0e\uff0e/{name}",
    "\u2215..\u2215{name}",
)

ASSET_REFERENCE = re.compile(
    r"""["'(]\s*(\.{1,2}/[^"')\s]+\.(?:js|css|svg))\s*["')]"""
)

MARKUP_REFERENCE = re.compile(r"""(?:href|src)="([^"]+)\"""")


def suffix_of(name):
    return name[name.rindex("."):]


def content_type_of(response):
    return response.headers["content-type"].split(";")[0].strip()


@pytest.fixture
def static_client(client_factory, scalar):
    return client_factory(scalar, prefix="/space")


def fetch(client, name):
    return client.get(f"/space/static/{name}")


@pytest.mark.parametrize("name", ALL_ASSETS)
def test_every_declared_asset_is_served(static_client, name):
    response = fetch(static_client, name)

    assert response.status_code == 200
    assert response.content


@pytest.mark.parametrize("name", ALL_ASSETS)
def test_every_declared_asset_carries_its_content_type(static_client, name):
    response = fetch(static_client, name)

    assert content_type_of(response) == EXPECTED_TYPES[suffix_of(name)]


def test_content_type_table_is_explicit():
    assert router_module.STATIC_TYPES == EXPECTED_TYPES


@pytest.mark.parametrize("name", ("page.js", "page.css", "icons/check.svg"))
def test_content_type_ignores_the_platform_mimetypes_registry(
    static_client, monkeypatch, name
):
    def guessed_as_plain_text(*args, **kwargs):
        return ("text/plain", None)

    monkeypatch.setattr("mimetypes.guess_type", guessed_as_plain_text)
    monkeypatch.setattr("starlette.responses.guess_type", guessed_as_plain_text)

    response = fetch(static_client, name)

    assert response.status_code == 200
    assert content_type_of(response) == EXPECTED_TYPES[suffix_of(name)]
    assert content_type_of(response) != "text/plain"


def test_static_response_carries_cache_headers(static_client):
    response = fetch(static_client, "page.js")

    assert response.headers["etag"]
    assert response.headers["cache-control"] == router_module.STATIC_CACHE


def test_matching_if_none_match_answers_304_without_body(static_client):
    first = fetch(static_client, "page.js")
    etag = first.headers["etag"]

    second = static_client.get(
        "/space/static/page.js", headers={"If-None-Match": etag}
    )

    assert second.status_code == 304
    assert second.content == b""
    assert second.headers["etag"] == etag
    assert second.headers["cache-control"] == router_module.STATIC_CACHE


def test_mismatched_if_none_match_serves_the_file_again(static_client):
    first = fetch(static_client, "page.js")

    second = static_client.get(
        "/space/static/page.js", headers={"If-None-Match": '"not-the-etag"'}
    )

    assert second.status_code == 200
    assert second.content == first.content


def test_etag_is_stable_while_the_file_does_not_change(static_client):
    etags = {fetch(static_client, "page.js").headers["etag"] for _ in range(3)}

    assert len(etags) == 1


def test_two_different_files_get_different_etags(static_client):
    page = fetch(static_client, "page.js").headers["etag"]
    output = fetch(static_client, "output.js").headers["etag"]

    assert page != output


def test_etag_changes_when_the_file_changes(
    client_factory, scalar, monkeypatch, tmp_path
):
    copy = tmp_path / "static"
    shutil.copytree(router_module.STATIC_ROOTS[0], copy)
    monkeypatch.setattr(router_module, "STATIC_ROOTS", (copy.resolve(),))

    client = client_factory(scalar, prefix="/space")
    before = fetch(client, "page.js").headers["etag"]

    (copy / "page.js").write_text("// replaced\n" * 40, encoding="utf-8")
    after = fetch(client, "page.js").headers["etag"]

    assert before != after


def test_subdirectory_assets_are_served_under_a_prefix(client_factory, scalar):
    client = client_factory(scalar, prefix="/deep/nest")

    response = client.get("/deep/nest/static/icons/trash.svg")

    assert response.status_code == 200
    assert content_type_of(response) == "image/svg+xml"


def test_subdirectory_assets_are_served_without_a_prefix(
    client_factory, scalar
):
    client = client_factory(scalar)

    response = client.get("/static/icons/copy.svg")

    assert response.status_code == 200
    assert response.content


@pytest.mark.parametrize("name", REJECTED_PATHS)
def test_rejected_paths_answer_404(static_client, name):
    response = fetch(static_client, name)

    assert response.status_code == 404


def test_rejections_do_not_distinguish_missing_from_forbidden(static_client):
    missing = fetch(static_client, "there-is-no-such-asset.js")
    forbidden = fetch(static_client, "../router.py")

    assert missing.status_code == forbidden.status_code == 404
    assert missing.json() == forbidden.json()


def test_no_vector_reads_a_real_repository_file(static_client, repo_root):
    targets = {
        "pyproject.toml": (repo_root / "pyproject.toml").read_bytes(),
        "router.py": (
            repo_root / "src" / "func_to_web" / "web" / "router.py"
        ).read_bytes(),
        "conftest.py": (repo_root / "tests" / "conftest.py").read_bytes(),
    }

    for target, content in targets.items():
        marker = content[:60]

        for vector in ESCAPE_VECTORS:
            for name in (target, f"src/func_to_web/web/{target}"):
                response = fetch(static_client, vector.format(name=name))

                assert response.status_code == 404, (vector, name)
                assert marker not in response.content, (vector, name)


def test_absurdly_long_static_paths_answer_404(static_client):
    for name in ("a" * 4000, "a/" * 2000 + "page.js", "../" * 1000 + "page.js"):
        response = fetch(static_client, name)

        assert response.status_code == 404


def test_crawl_of_the_real_graph_reaches_every_page_asset(client_factory,
                                                          scalar):
    client = client_factory(scalar, prefix="/mounted")
    page_url = "http://testserver/mounted/add/"
    page = client.get(page_url)

    assert page.status_code == 200

    pending = [
        (page_url, reference)
        for reference in MARKUP_REFERENCE.findall(page.text)
    ]
    visited = {}

    while pending:
        base, reference = pending.pop()
        url = urljoin(base, reference)

        if url in visited:
            continue

        response = client.get(url)
        visited[url] = response.status_code

        if response.status_code != 200:
            continue

        if url.endswith(".js") or url.endswith(".css"):
            pending.extend(
                (url, found) for found in ASSET_REFERENCE.findall(response.text)
            )

    assert set(visited.values()) == {200}

    reached = {
        url.removeprefix("http://testserver/mounted/static/")
        for url in visited
    }

    assert reached == set(CRAWLED_ASSETS)
    assert len(visited) == 21


def refusing_resolve(root):
    resolve = Path.resolve

    def refuse(self, *args, **kwargs):
        if str(self).startswith(str(root)):
            raise OSError(22, "Invalid argument")

        return resolve(self, *args, **kwargs)

    return refuse


def test_a_root_that_cannot_be_resolved_does_not_hide_the_next_one(monkeypatch):
    first, second = router_module.STATIC_ROOTS

    monkeypatch.setattr(Path, "resolve", refusing_resolve(first))

    found = router_module.static_asset("widgets.css")

    assert found is not None
    assert found.is_relative_to(second)
    assert found.is_file()


def test_the_asset_of_the_second_root_is_still_served_over_http(
    static_client, monkeypatch
):
    first, _ = router_module.STATIC_ROOTS

    monkeypatch.setattr(Path, "resolve", refusing_resolve(first))

    response = fetch(static_client, "widgets.css")

    assert response.status_code == 200
    assert content_type_of(response) == "text/css"


def test_an_asset_that_no_root_holds_is_not_found():
    assert router_module.static_asset("no-such-asset.js") is None


def test_no_root_left_to_try_is_not_found(monkeypatch):
    def refuse(self, *args, **kwargs):
        raise OSError(22, "Invalid argument")

    monkeypatch.setattr(Path, "resolve", refuse)

    assert router_module.static_asset("page.js") is None
