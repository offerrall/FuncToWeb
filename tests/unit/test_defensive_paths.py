import asyncio
import sys
import threading
from pathlib import Path
from urllib.parse import unquote

import pytest

import func_to_web.web.router as router_module
from func_to_web import WebFunction, page_of
from func_to_web.web.print_capture import PrintCapture, install
from func_to_web.web.references import segment_of, stored_of
from func_to_web.web.returned_files import stored_return
from func_to_web.web.router import DefensivePaths, static_asset


def add(a: int = 1) -> str:
    """Adds."""
    return str(a)


@pytest.mark.parametrize("value", [None, add, "add", 3, WebFunction])
def test_page_of_refuses_anything_but_a_web_function(value):
    with pytest.raises(TypeError, match="web_function must be WebFunction"):
        page_of(value)


def test_nested_sync_captures_restore_the_outer_one():
    outer = PrintCapture()
    inner = PrintCapture()

    with outer.capture_sync():
        print("outer first")

        with inner.capture_sync():
            print("inner only")

        print("outer again")

    assert "".join(inner.drain()) == "inner only\n"
    assert "".join(outer.drain()) == "outer first\nouter again\n"


def test_the_installed_stdout_delegates_unknown_attributes():
    install()

    assert sys.stdout.encoding == sys.stdout._original.encoding
    assert sys.stdout.isatty() == sys.stdout._original.isatty()

    with pytest.raises(AttributeError):
        sys.stdout.this_attribute_does_not_exist


def test_a_path_the_system_cannot_resolve_is_not_a_stored_file(monkeypatch,
                                                               tmp_path):
    resolve = Path.resolve

    def refuse(self, *args, **kwargs):
        if self.name == "a.txt":
            raise OSError(22, "Invalid argument")

        return resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", refuse)

    with pytest.raises(ValueError, match="is not a usable path"):
        stored_of("a.txt", tmp_path)


def test_an_unresolvable_static_name_is_not_served(monkeypatch):
    def refuse(self, *args, **kwargs):
        raise OSError(22, "Invalid argument")

    monkeypatch.setattr(Path, "resolve", refuse)

    assert router_module.static_asset("page.js") is None


def test_the_last_shape_rule_is_unreachable_from_the_earlier_ones():
    # segment_of ends with a Path() check that no accepted string can fail:
    # separators, colons, control characters and reserved names are already
    # refused above it. It stays as the last line of defence, so this test
    # states why coverage never reaches it instead of pretending it does.
    for reference in ("a.txt", "a" * 200, ".hidden", "a-b_c.tar.gz"):
        assert segment_of(reference) == reference
        assert Path(reference).name == reference
        assert not Path(reference).is_absolute()


# --- The DefensivePaths middleware, without a client in the way -------------
#
# httpx resolves dot segments before the request leaves, as RFC 3986 asks, so
# no integration test can ever deliver "/static/.." to the server: it arrives
# as "/". Every case below therefore writes the ASGI scope by hand, which is
# what a hostile client -- one that does not follow the RFC -- puts on the wire.

REFUSED_RAW_PATHS = [
    b"/static/..",
    b"/static/../router.py",
    b"/static/%2e%2e",
    b"/static/%2e%2e/router.py",
    b"/returns/..",
    b"/returns/../secret.txt",
    b"/..",
    b"/add/../../etc/passwd",
]

ALLOWED_RAW_PATHS = [
    b"/",
    b"/add/",
    b"/add/invoke",
    b"/doc",
    b"/static/app.css",
    b"/returns/0123456789abcdef0123456789abcdef.report.txt",
    b"/static/..dots.css",
    b"/static/a..b.css",
]


class Inner:
    """The application DefensivePaths wraps: it records that it was reached."""

    def __init__(self) -> None:
        self.scopes = []

    async def __call__(self, scope, receive, send) -> None:
        self.scopes.append(scope)
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain")],
        })
        await send({"type": "http.response.body", "body": b"inner"})


def scope_of(raw_path=None, path=None, query=b""):
    """An http scope with only what the middleware and a Response read."""
    scope = {
        "type": "http",
        "method": "GET",
        "headers": [],
        "query_string": query,
        "path": "/" if path is None else path,
    }

    if raw_path is not None:
        scope["raw_path"] = raw_path

    return scope


def drive(coroutine):
    """Run one coroutine to completion whatever the calling thread is doing.

    The e2e suite keeps Playwright's own event loop alive in the main thread
    for the whole session, and asyncio.run() refuses to nest inside a running
    loop, so the loop is opened in a thread of its own. That way these tests
    do not depend on which suites ran before them.
    """
    box = {}

    def work():
        try:
            box["value"] = asyncio.run(coroutine)
        except BaseException as error:  # noqa: BLE001 - re-raised below
            box["error"] = error

    thread = threading.Thread(target=work)
    thread.start()
    thread.join()

    if "error" in box:
        raise box["error"]

    return box["value"]


def call(scope):
    """Drive the middleware over one scope and report status and inner app."""
    inner = Inner()
    app = DefensivePaths(inner)
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    drive(app(scope, receive, send))

    started = [m for m in messages if m["type"] == "http.response.start"]
    body = b"".join(m.get("body", b"") for m in messages
                    if m["type"] == "http.response.body")

    return {
        "status": started[0]["status"] if started else None,
        "body": body,
        "reached": inner.scopes != [],
    }


@pytest.mark.parametrize("raw_path", REFUSED_RAW_PATHS)
def test_a_dot_segment_never_reaches_the_application(raw_path):
    answered = call(scope_of(raw_path=raw_path))

    assert answered["status"] == 404
    assert not answered["reached"]
    assert answered["body"] == b'{"detail":"Not Found"}'


@pytest.mark.parametrize("raw_path", ALLOWED_RAW_PATHS)
def test_an_ordinary_path_is_handed_to_the_application(raw_path):
    answered = call(scope_of(raw_path=raw_path))

    assert answered["status"] == 200
    assert answered["reached"]
    assert answered["body"] == b"inner"


def test_a_query_string_of_its_own_is_not_read_as_a_segment():
    answered = call(scope_of(raw_path=b"/add/?prefill=%7B%22a%22%3A%22..%22%7D"))

    assert answered["status"] == 200
    assert answered["reached"]


def test_a_dot_segment_in_the_query_string_of_the_raw_path_is_ignored():
    answered = call(scope_of(raw_path=b"/add/?next=/static/.."))

    assert answered["status"] == 200
    assert answered["reached"]


# The fallback: raw_path is optional in ASGI. A server that never populates it
# would otherwise leave the middleware reading b"" and defending nothing.
@pytest.mark.parametrize("path", ["/static/..", "/static/../router.py",
                                  "/returns/..", "/.."])
def test_a_scope_without_raw_path_is_defended_through_path(path):
    answered = call(scope_of(raw_path=None, path=path))

    assert answered["status"] == 404
    assert not answered["reached"]


@pytest.mark.parametrize("path", ["/", "/add/", "/static/app.css"])
def test_a_scope_without_raw_path_still_serves_an_ordinary_path(path):
    answered = call(scope_of(raw_path=None, path=path))

    assert answered["status"] == 200
    assert answered["reached"]


@pytest.mark.parametrize("path", ["/static/..", "/returns/.."])
def test_an_empty_raw_path_falls_back_to_path(path):
    answered = call(scope_of(raw_path=b"", path=path))

    assert answered["status"] == 404
    assert not answered["reached"]


def test_a_scope_that_is_not_http_is_never_answered_with_a_response():
    inner = Inner()
    app = DefensivePaths(inner)
    messages = []

    async def receive():
        return {"type": "lifespan.startup"}

    async def send(message):
        messages.append(message)

    drive(app({"type": "lifespan"}, receive, send))

    assert inner.scopes != []


# An encoded backslash is not a dot segment: unquote_to_bytes turns "..%5c"
# into b"..\\", which is one segment and not b"..", so DefensivePaths lets it
# through on purpose. What refuses it is the layer behind, and these are the
# three doors it can knock on.
BACKSLASH = "..%5c"


def test_defensive_paths_does_not_claim_to_stop_an_encoded_backslash():
    answered = call(scope_of(raw_path=f"/static/{BACKSLASH}".encode("utf-8")))

    assert answered["status"] == 200
    assert answered["reached"]


def test_the_static_layer_refuses_an_encoded_backslash():
    assert static_asset(unquote(BACKSLASH)) is None
    assert static_asset(unquote(f"{BACKSLASH}router.py")) is None
    assert static_asset(f"{BACKSLASH}router.py") is None


def test_the_returns_layer_refuses_an_encoded_backslash():
    with pytest.raises(ValueError):
        stored_return(unquote(f"{BACKSLASH}secret.txt"))

    with pytest.raises(FileNotFoundError):
        stored_return(f"{BACKSLASH}secret.txt")


def test_the_reference_frontier_refuses_an_encoded_backslash():
    with pytest.raises(ValueError):
        segment_of(unquote(f"{BACKSLASH}secret.txt"))
