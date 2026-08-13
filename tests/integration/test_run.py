from typing import Annotated

import pytest
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.testclient import TestClient

from func_to_web import (
    Download,
    FileHint,
    WebFunction,
    WebFunctions,
    run,
)

TxtFile = Annotated[str, FileHint(extensions=(".txt",))]


def add(a: int, b: int = 2) -> int:
    """Adds two numbers."""
    return a + b


def multiply(a: int, b: int = 3) -> int:
    """Multiplies two numbers."""
    return a * b


def read(document: TxtFile) -> str:
    """Reads a file."""
    return document


def bundle() -> Annotated[bytes, Download(filename="r.bin")]:
    """Returns a file."""
    return b"xxxx"


def chatty(times: int = 2) -> str:
    """Prints before returning."""
    for index in range(times):
        print(f"line {index}")
    return "done"


@pytest.fixture
def served(monkeypatch):
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(uvicorn, "run", fake_run)
    return calls


def application_of(calls):
    (args, _), = calls
    return args[0]


def options_of(calls):
    (_, kwargs), = calls
    return kwargs


def routes_of(app):
    return [(route.path, tuple(sorted(route.methods - {"HEAD"})))
            for route in app.routes if isinstance(route, Route)]


def paths_of(app):
    return [path for path, _ in routes_of(app)]


def test_a_callable_is_accepted(served):
    run(add)

    assert "/add/" in paths_of(application_of(served))


def test_a_web_function_is_accepted(served):
    run(WebFunction(add, slug="sum"))

    assert "/sum/" in paths_of(application_of(served))


def test_an_iterable_is_accepted(served):
    run([add, multiply])

    assert "/add/" in paths_of(application_of(served))
    assert "/multiply/" in paths_of(application_of(served))


def test_a_generator_is_accepted(served):
    run(entry for entry in (add, multiply))

    assert "/add/" in paths_of(application_of(served))
    assert "/multiply/" in paths_of(application_of(served))


def test_a_prepared_space_is_accepted(served):
    run(WebFunctions((WebFunction(add),), title="Prepared"))

    assert application_of(served).title == "Prepared"


def test_the_space_order_is_kept(served):
    run([multiply, add])

    assert paths_of(application_of(served))[:6] == [
        "/multiply/", "/multiply/invoke", "/multiply/invoke-stream",
        "/add/", "/add/invoke", "/add/invoke-stream",
    ]


def test_a_starlette_application_is_built(served):
    run(add)

    assert isinstance(application_of(served), Starlette)


def test_the_router_is_mounted_at_the_root(served):
    run(add)

    assert routes_of(application_of(served)) == [
        ("/add/", ("GET",)),
        ("/add/invoke", ("POST",)),
        ("/add/invoke-stream", ("POST",)),
        ("/doc", ("GET",)),
        ("/static/{name:path}", ("GET",)),
        ("/", ("GET",)),
    ]


def test_the_index_route_is_added_last(served):
    run(add)

    assert routes_of(application_of(served))[-1] == ("/", ("GET",))


def test_the_index_lists_every_function_of_the_space(served):
    run([add, multiply])

    with TestClient(application_of(served)) as client:
        html = client.get("/").text

    assert 'data-slug="add"' in html
    assert 'data-slug="multiply"' in html


def test_the_index_is_the_only_route_run_adds_over_the_router(served):
    run([add, read])

    assert paths_of(application_of(served)) == [
        "/add/", "/add/invoke", "/add/invoke-stream",
        "/read/", "/read/invoke", "/read/invoke-stream",
        "/upload", "/doc", "/static/{name:path}", "/",
    ]


def test_the_default_host_is_the_loopback_address(served):
    run(add)

    assert options_of(served)["host"] == "127.0.0.1"


def test_the_default_port_is_8000(served):
    run(add)

    assert options_of(served)["port"] == 8000


def test_the_host_and_the_port_are_forwarded(served):
    run(add, host="0.0.0.0", port=9123)

    assert options_of(served)["host"] == "0.0.0.0"
    assert options_of(served)["port"] == 9123


def test_uvicorn_receives_exactly_the_application_host_and_port(served):
    run(add)

    assert served == [((application_of(served),),
                       {"host": "127.0.0.1", "port": 8000})]


def test_uvicorn_is_called_once(served):
    run(add)

    assert len(served) == 1


def test_the_title_names_the_application(served):
    run(add, title="Internal tools")

    assert application_of(served).title == "Internal tools"


def test_the_default_title_is_func_to_web(served):
    run(add)

    assert application_of(served).title == "FuncToWeb"


def test_the_title_reaches_the_document_and_the_index(served):
    run(add, title="Internal tools")

    with TestClient(application_of(served)) as client:
        assert "Internal tools" in client.get("/doc").text
        assert "Internal tools" in client.get("/").text


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_the_theme_reaches_the_index_and_every_page(served, html_root, theme):
    run(add, theme=theme)

    with TestClient(application_of(served)) as client:
        index = client.get("/").text
        page = client.get("/add/").text

    assert html_root(index) == f'<html data-pth-theme="{theme}">'
    assert html_root(page) == f'<html data-pth-theme="{theme}">'


def test_the_system_theme_leaves_the_html_tag_bare(served, html_root):
    run(add)

    with TestClient(application_of(served)) as client:
        assert html_root(client.get("/").text) == "<html>"


def test_capture_prints_reaches_the_router(served, sse):
    run(chatty, capture_prints=False)

    with TestClient(application_of(served)) as client:
        response = client.post("/chatty/invoke-stream", json={"times": 2})

    assert [name for name, _ in sse(response.text)] == ["start", "result"]


def test_capture_prints_defaults_to_capturing(served, sse):
    run(chatty)

    with TestClient(application_of(served)) as client:
        response = client.post("/chatty/invoke-stream", json={"times": 2})

    assert "print" in [name for name, _ in sse(response.text)]


def test_max_upload_bytes_reaches_the_router(served):
    run(read, max_upload_bytes=4)

    with TestClient(application_of(served)) as client:
        response = client.post("/upload", content=b"x" * 40,
                               headers={"X-File-Reference": "a.txt"})

    assert response.status_code == 413


def test_the_storage_directories_reach_the_router(served, tmp_path):
    uploads = tmp_path / "run-uploads"
    returns = tmp_path / "run-returns"

    run([read, bundle], uploads_dir=uploads, returns_dir=returns)

    with TestClient(application_of(served)) as client:
        stored = client.post("/upload", content=b"body",
                             headers={"X-File-Reference": "a.txt"})
        result = client.post("/bundle/invoke", json={}).json()["result"]

    assert stored.status_code == 200
    assert len(list(uploads.iterdir())) == 1
    assert [entry.name for entry in returns.iterdir()] == [result["value"]]


def test_the_effective_directories_are_announced(served, capsys, tmp_path):
    uploads = tmp_path / "run-uploads"
    returns = tmp_path / "run-returns"

    run([read, bundle], uploads_dir=uploads, returns_dir=returns)

    printed = capsys.readouterr().out

    assert f"UPLOADS DIR: {uploads}\n" in printed
    assert f"RETURNS DIR: {returns}\n" in printed


def test_an_unusable_storage_directory_is_refused_before_uvicorn_runs(served,
                                                                      tmp_path):
    occupied = tmp_path / "taken.txt"
    occupied.write_bytes(b"x")

    with pytest.raises(ValueError, match="uploads_dir is not a directory"):
        run(add, uploads_dir=occupied)

    assert served == []


def test_uvicorn_kwargs_are_forwarded(served):
    run(add, uvicorn_kwargs={"log_level": "debug", "workers": 1})

    assert options_of(served) == {
        "host": "127.0.0.1",
        "port": 8000,
        "log_level": "debug",
        "workers": 1,
    }


def test_the_caller_mappings_are_never_modified(served):
    server_options = {"log_level": "debug"}

    run(add, uvicorn_kwargs=server_options)

    assert server_options == {"log_level": "debug"}


def test_host_in_uvicorn_kwargs_is_refused(served):
    with pytest.raises(TypeError, match="cannot contain 'host'"):
        run(add, uvicorn_kwargs={"host": "0.0.0.0"})


def test_port_in_uvicorn_kwargs_is_refused(served):
    with pytest.raises(TypeError, match="cannot contain 'port'"):
        run(add, uvicorn_kwargs={"port": 9000})


def test_app_in_uvicorn_kwargs_is_refused(served):
    with pytest.raises(TypeError, match="cannot contain 'app'"):
        run(add, uvicorn_kwargs={"app": Starlette()})


@pytest.mark.parametrize("options", [
    {"uvicorn_kwargs": {"host": "0.0.0.0"}},
    {"uvicorn_kwargs": {"port": 9000}},
    {"uvicorn_kwargs": {"app": "x"}},
])
def test_an_owned_key_is_refused_before_uvicorn_runs(served, options):
    with pytest.raises(TypeError):
        run(add, **options)

    assert served == []


def test_an_empty_space_is_refused_before_uvicorn_runs(served):
    with pytest.raises(ValueError, match="at least one function"):
        run([])

    assert served == []


def test_a_non_callable_space_is_refused_before_uvicorn_runs(served):
    with pytest.raises(TypeError, match="entries must be callables"):
        run(3)

    assert served == []


def test_a_duplicated_slug_is_refused_before_uvicorn_runs(served):
    with pytest.raises(ValueError, match="share the slug"):
        run([add, WebFunction(multiply, slug="add")])

    assert served == []


def test_an_unknown_theme_is_refused_before_uvicorn_runs(served):
    with pytest.raises(ValueError, match="theme must be one of"):
        run(add, theme="Dark")

    assert served == []


def test_an_invalid_max_upload_bytes_is_refused_before_uvicorn_runs(served):
    with pytest.raises(ValueError, match="greater than zero"):
        run(add, max_upload_bytes=0)

    assert served == []


def test_a_prepared_space_with_a_title_is_refused_before_uvicorn_runs(served):
    space = WebFunctions((WebFunction(add),), title="Prepared")

    with pytest.raises(TypeError, match="already carries its title"):
        run(space, title="Other")

    assert served == []


def test_run_returns_none(served):
    assert run(add) is None
