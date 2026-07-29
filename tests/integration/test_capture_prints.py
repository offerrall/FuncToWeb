import io
import os
import subprocess
import sys
import threading

import pytest

from func_to_web import WebFunction

IMPORT_ONLY = """
import sys
import func_to_web
print(type(sys.stdout).__name__)
"""

BUILD_WEB_FUNCTION = """
import sys
from func_to_web import WebFunction

def chatty(times: int = 1) -> str:
    print("hello")
    return "done"

WebFunction(chatty)
print(type(sys.stdout).__name__)
"""

BUILD_ROUTER = """
import sys
from func_to_web import router_of

def chatty(times: int = 1) -> str:
    print("hello")
    return "done"

router_of(chatty, capture_prints=True)
print(type(sys.stdout).__name__)
"""

PLAIN_INVOKE = """
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient
from func_to_web import router_of

def chatty(times: int = 1) -> str:
    print("hello")
    return "done"

app = FastAPI()
app.include_router(router_of(chatty, capture_prints=True))
TestClient(app).post("/chatty/invoke", json={"times": 1})
print(type(sys.stdout).__name__)
"""

STREAM_WITHOUT_CAPTURE = """
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient
from func_to_web import router_of

def chatty(times: int = 1) -> str:
    print("hello")
    return "done"

app = FastAPI()
app.include_router(router_of(chatty, capture_prints=False))
TestClient(app).post("/chatty/invoke-stream", json={"times": 1})
print(type(sys.stdout).__name__)
"""

STREAM_WITH_CAPTURE = """
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient
from func_to_web import router_of

def chatty(times: int = 1) -> str:
    print("hello")
    return "done"

app = FastAPI()
app.include_router(router_of(chatty, capture_prints=True))
TestClient(app).post("/chatty/invoke-stream", json={"times": 1})
print(type(sys.stdout).__name__)
"""


def stdout_type_after(repo_root, script):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(repo_root / "src")
    environment["PYTHONIOENCODING"] = "utf-8"

    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=environment,
        cwd=str(repo_root),
        timeout=180,
    )

    assert completed.returncode == 0, completed.stderr

    return completed.stdout.strip().splitlines()[-1]


def names_of(events):
    return [name for name, _ in events]


def printed_text(events):
    return "".join(payload["text"]
                   for name, payload in events if name == "print")


def chatty(times: int = 1) -> str:
    for index in range(times):
        print(f"line {index}")

    return "done"


def stream_of(client, sse, slug="chatty", **data):
    return sse(client.post(f"/{slug}/invoke-stream", json=data).text)


def test_importing_the_package_does_not_replace_stdout(repo_root):
    assert stdout_type_after(repo_root, IMPORT_ONLY) != "_Dispatcher"


def test_building_a_web_function_does_not_replace_stdout(repo_root):
    assert stdout_type_after(repo_root, BUILD_WEB_FUNCTION) != "_Dispatcher"


def test_building_a_router_does_not_replace_stdout(repo_root):
    assert stdout_type_after(repo_root, BUILD_ROUTER) != "_Dispatcher"


def test_plain_invoke_does_not_replace_stdout(repo_root):
    assert stdout_type_after(repo_root, PLAIN_INVOKE) != "_Dispatcher"


def test_stream_without_capture_does_not_replace_stdout(repo_root):
    assert stdout_type_after(repo_root, STREAM_WITHOUT_CAPTURE) != "_Dispatcher"


def test_stream_with_capture_installs_the_dispatcher_lazily(repo_root):
    assert stdout_type_after(repo_root, STREAM_WITH_CAPTURE) == "_Dispatcher"


def test_both_unset_captures_by_default(client_factory, sse):
    client = client_factory(WebFunction(chatty, capture_prints=None))

    events = stream_of(client, sse, times=2)

    assert printed_text(events) == "line 0\nline 1\n"
    assert names_of(events).count("print") >= 1


def test_router_true_with_function_unset_captures(client_factory, sse):
    client = client_factory(WebFunction(chatty, capture_prints=None),
                            capture_prints=True)

    events = stream_of(client, sse, times=2)

    assert printed_text(events) == "line 0\nline 1\n"


def test_router_false_with_function_unset_does_not_capture(
    client_factory, sse
):
    client = client_factory(WebFunction(chatty, capture_prints=None),
                            capture_prints=False)

    events = stream_of(client, sse, times=2)

    assert names_of(events) == ["start", "result"]
    assert printed_text(events) == ""


def test_function_true_beats_router_false(client_factory, sse):
    client = client_factory(WebFunction(chatty, capture_prints=True),
                            capture_prints=False)

    events = stream_of(client, sse, times=2)

    assert printed_text(events) == "line 0\nline 1\n"


def test_function_false_beats_router_true(client_factory, sse):
    client = client_factory(WebFunction(chatty, capture_prints=False),
                            capture_prints=True)

    events = stream_of(client, sse, times=2)

    assert names_of(events) == ["start", "result"]
    assert printed_text(events) == ""


def test_run_hands_capture_prints_to_the_router(monkeypatch, sse):
    import uvicorn
    from fastapi.testclient import TestClient

    from func_to_web import run

    built = {}

    def fake_run(app, **options):
        built["app"] = app

    monkeypatch.setattr(uvicorn, "run", fake_run)

    run(chatty, capture_prints=False)

    with TestClient(built["app"]) as client:
        events = stream_of(client, sse, times=2)

    assert names_of(events) == ["start", "result"]


def test_function_setting_beats_run(monkeypatch, sse):
    import uvicorn
    from fastapi.testclient import TestClient

    from func_to_web import run

    built = {}

    def fake_run(app, **options):
        built["app"] = app

    monkeypatch.setattr(uvicorn, "run", fake_run)

    run(WebFunction(chatty, capture_prints=True), capture_prints=False)

    with TestClient(built["app"]) as client:
        events = stream_of(client, sse, times=2)

    assert printed_text(events) == "line 0\nline 1\n"


def test_print_is_captured_for_the_matching_execution(client_factory, sse):
    def one(a: int = 1) -> str:
        print("from one")
        return "1"

    def two(a: int = 1) -> str:
        print("from two")
        return "2"

    client = client_factory([one, two])

    first = stream_of(client, sse, slug="one", a=1)
    second = stream_of(client, sse, slug="two", a=1)

    assert printed_text(first) == "from one\n"
    assert printed_text(second) == "from two\n"


def test_print_outside_an_execution_reaches_the_normal_stdout(
    client_factory, monkeypatch, sse
):
    def quiet(a: int = 1) -> str:
        return "q"

    client = client_factory([WebFunction(chatty), quiet])
    console = io.StringIO()
    monkeypatch.setattr(sys, "stdout", console)

    stream_of(client, sse, times=1)

    print("outside any execution")

    events = stream_of(client, sse, slug="quiet", a=1)

    assert names_of(events) == ["start", "result"]
    assert console.getvalue() == "line 0\noutside any execution\n"


def test_captured_print_still_reaches_the_real_stdout(
    client_factory, monkeypatch, sse
):
    client = client_factory(WebFunction(chatty))
    console = io.StringIO()
    monkeypatch.setattr(sys, "stdout", console)

    events = stream_of(client, sse, times=3)

    assert printed_text(events) == "line 0\nline 1\nline 2\n"
    assert console.getvalue() == "line 0\nline 1\nline 2\n"


def test_stdout_is_restored_after_a_function_error(
    client_factory, monkeypatch, sse
):
    def crashing(a: int = 1) -> str:
        print("before the crash")
        raise RuntimeError("crashed")

    def quiet(a: int = 1) -> str:
        return "q"

    client = client_factory([crashing, quiet])
    console = io.StringIO()
    monkeypatch.setattr(sys, "stdout", console)

    failed = stream_of(client, sse, slug="crashing", a=1)

    print("after the crash")

    events = stream_of(client, sse, slug="quiet", a=1)

    assert failed[-1][1] == {"error": "RuntimeError: crashed"}
    assert printed_text(failed) == "before the crash\n"
    assert names_of(events) == ["start", "result"]
    assert console.getvalue() == "before the crash\nafter the crash\n"


def test_stderr_is_not_captured(client_factory, monkeypatch, sse):
    def mixed(a: int = 1) -> str:
        print("to stdout")
        print("to stderr", file=sys.stderr)
        return "ok"

    client = client_factory(mixed)
    errors = io.StringIO()
    monkeypatch.setattr(sys, "stderr", errors)

    events = stream_of(client, sse, slug="mixed", a=1)

    assert printed_text(events) == "to stdout\n"
    assert errors.getvalue() == "to stderr\n"


def test_concurrent_executions_do_not_mix_their_prints(client_factory, sse):
    barrier = threading.Barrier(2, timeout=60)

    def alpha(a: int = 1) -> str:
        for index in range(5):
            barrier.wait()
            print(f"alpha {index}")

        return "alpha"

    def beta(a: int = 1) -> str:
        for index in range(5):
            barrier.wait()
            print(f"beta {index}")

        return "beta"

    client = client_factory([alpha, beta])
    bodies = {}

    def fire(slug):
        bodies[slug] = client.post(f"/{slug}/invoke-stream",
                                   json={"a": 1}).text

    threads = [threading.Thread(target=fire, args=(slug,))
               for slug in ("alpha", "beta")]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join(60)

    assert not any(thread.is_alive() for thread in threads)

    expected_alpha = "".join(f"alpha {index}\n" for index in range(5))
    expected_beta = "".join(f"beta {index}\n" for index in range(5))

    assert printed_text(sse(bodies["alpha"])) == expected_alpha
    assert printed_text(sse(bodies["beta"])) == expected_beta


def test_print_from_a_nested_function_is_captured(client_factory, sse):
    def helper(depth):
        print(f"depth {depth}")

        if depth:
            helper(depth - 1)

    def outer(a: int = 1) -> str:
        helper(2)

        return "ok"

    client = client_factory(outer)

    events = stream_of(client, sse, slug="outer", a=1)

    assert printed_text(events) == "depth 2\ndepth 1\ndepth 0\n"


def test_print_from_a_thread_started_by_the_function_is_not_captured(
    client_factory, monkeypatch, sse
):
    def spawner(a: int = 1) -> str:
        def worker():
            print("from the spawned thread")

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(60)

        print("from the function")

        return "ok"

    client = client_factory(spawner)
    console = io.StringIO()
    monkeypatch.setattr(sys, "stdout", console)

    events = stream_of(client, sse, slug="spawner", a=1)

    assert printed_text(events) == "from the function\n"
    assert console.getvalue() == (
        "from the spawned thread\nfrom the function\n"
    )


def test_flush_is_captured_and_forwarded(client_factory, monkeypatch, sse):
    def flushing(a: int = 1) -> str:
        print("flushed line", flush=True)
        sys.stdout.write("written")
        sys.stdout.flush()

        return "ok"

    client = client_factory(flushing)
    console = io.StringIO()
    monkeypatch.setattr(sys, "stdout", console)

    events = stream_of(client, sse, slug="flushing", a=1)

    assert printed_text(events) == "flushed line\nwritten"
    assert console.getvalue() == "flushed line\nwritten"


def test_partial_write_without_newline_is_captured(client_factory, sse):
    def fragment(a: int = 1) -> str:
        sys.stdout.write("half a ")
        sys.stdout.write("line")

        return "ok"

    client = client_factory(fragment)

    events = stream_of(client, sse, slug="fragment", a=1)

    assert printed_text(events) == "half a line"


def test_empty_write_produces_no_print_event(client_factory, sse):
    def blank(a: int = 1) -> str:
        sys.stdout.write("")

        return "ok"

    client = client_factory(blank)

    events = stream_of(client, sse, slug="blank", a=1)

    assert names_of(events) == ["start", "result"]


@pytest.mark.parametrize("declared", ["yes", 1, 0.0, []])
def test_capture_prints_rejects_non_boolean(declared):
    with pytest.raises(TypeError):
        WebFunction(chatty, capture_prints=declared)
