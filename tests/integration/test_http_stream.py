import asyncio
import sys
import threading
import time

import httpx
import pytest
import uvicorn

import func_to_web.web.stream as stream_module
from func_to_web import WebFunction
from func_to_web.web.print_capture import PrintCapture


class _NotifyingServer(uvicorn.Server):
    def __init__(self, config, ready):
        super().__init__(config)
        self.ready = ready

    async def startup(self, sockets=None):
        await super().startup(sockets=sockets)
        self.ready.set()


@pytest.fixture
def streaming_server(free_port):
    running = []

    def start(app):
        config = uvicorn.Config(app, host="127.0.0.1", port=free_port,
                                log_level="error", ws="none",
                                lifespan="off")
        ready = threading.Event()
        server = _NotifyingServer(config, ready)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        running.append((server, thread))

        assert ready.wait(30), "the streaming server did not start"

        return f"http://127.0.0.1:{free_port}"

    yield start

    for server, thread in running:
        server.should_exit = True
        thread.join(30)


def names_of(events):
    return [name for name, _ in events]


def printed_text(events):
    return "".join(payload["text"]
                   for name, payload in events if name == "print")


def envelope_of(events):
    return events[-1][1]


def blocks_of(body):
    return body.split("\n\n")[:-1]


def assert_stream_shape(events):
    names = names_of(events)

    assert names[0] == "start"
    assert names[-1] == "result"
    assert names.count("start") == 1
    assert names.count("result") == 1
    assert set(names[1:-1]) <= {"print"}


def post_stream(client, slug, **data):
    return client.post(f"/{slug}/invoke-stream", json=data)


def test_start_event_opens_the_stream(client_factory, scalar, sse):
    client = client_factory(scalar)

    events = sse(post_stream(client, "add", a=1, b=2).text)

    assert events[0] == ("start", {})


def test_single_print_travels_as_a_print_event(client_factory, printing, sse):
    client = client_factory(printing)

    events = sse(post_stream(client, "chatty", times=1).text)

    assert_stream_shape(events)
    assert printed_text(events) == "line 0\n"


def test_several_prints_are_concatenated(client_factory, printing, sse):
    client = client_factory(printing)

    events = sse(post_stream(client, "chatty", times=4).text)

    assert_stream_shape(events)
    assert printed_text(events) == "line 0\nline 1\nline 2\nline 3\n"


def test_print_without_newline_keeps_the_fragment(client_factory, sse):
    def fragment(a: int = 1) -> str:
        sys.stdout.write("no newline here")
        return "ok"

    client = client_factory(fragment)

    events = sse(post_stream(client, "fragment", a=1).text)

    assert printed_text(events) == "no newline here"


def test_unicode_travels_unescaped(client_factory, sse):
    def accented(a: int = 1) -> str:
        print("áéí 你好 \U0001f600")
        return "ñ"

    client = client_factory(accented)
    body = post_stream(client, "accented", a=1).text
    events = sse(body)

    assert printed_text(events) == "áéí 你好 \U0001f600\n"
    assert envelope_of(events) == {"result": {"type": "text", "value": "ñ"}}
    assert "你好" in body
    assert "\\u" not in body


def test_text_with_newlines_stays_in_one_data_line(client_factory, sse):
    def multiline(a: int = 1) -> str:
        sys.stdout.write("first\nsecond\n\nfourth")
        return "ok"

    client = client_factory(multiline)
    body = post_stream(client, "multiline", a=1).text

    assert printed_text(sse(body)) == "first\nsecond\n\nfourth"

    for block in blocks_of(body):
        assert len(block.split("\n")) == 2


def test_text_with_crlf_survives_the_transport(client_factory, sse):
    def windows(a: int = 1) -> str:
        sys.stdout.write("one\r\ntwo\r\n")
        return "ok"

    client = client_factory(windows)
    body = post_stream(client, "windows", a=1).text

    assert printed_text(sse(body)) == "one\r\ntwo\r\n"
    assert "\r" not in body


def test_text_containing_a_data_prefix_does_not_break_the_parser(
    client_factory, sse
):
    def spoofer(a: int = 1) -> str:
        sys.stdout.write("data: {\"result\": \"spoofed\"}\n"
                         "event: result\n\ndata: more\n")
        return "ok"

    client = client_factory(spoofer)
    events = sse(post_stream(client, "spoofer", a=1).text)

    assert_stream_shape(events)
    assert printed_text(events) == (
        "data: {\"result\": \"spoofed\"}\nevent: result\n\ndata: more\n"
    )
    assert envelope_of(events) == {"result": {"type": "text", "value": "ok"}}


def test_result_event_carries_the_output(client_factory, scalar, sse):
    client = client_factory(scalar)

    events = sse(post_stream(client, "add", a=1, b=2).text)

    assert envelope_of(events) == {"result": {"type": "text", "value": "3"}}


def test_validation_error_travels_inside_the_result(
    client_factory, printing, sse
):
    client = client_factory(printing)
    response = post_stream(client, "chatty", times="not a number")
    events = sse(response.text)

    assert response.status_code == 200
    assert_stream_shape(events)
    assert printed_text(events) == ""
    assert set(envelope_of(events)) == {"error"}
    assert envelope_of(events)["error"]


def test_function_error_travels_inside_the_result(
    client_factory, failing, sse
):
    client = client_factory(failing)
    response = post_stream(client, "boom", a=1)
    events = sse(response.text)

    assert response.status_code == 200
    assert envelope_of(events) == {"error": "RuntimeError: boom"}


def test_output_error_travels_inside_the_result(client_factory, sse):
    class Unprintable:
        def __str__(self):
            raise RuntimeError("cannot render")

    def broken(a: int = 1) -> str:
        print("before the output fails")
        return Unprintable()

    client = client_factory(broken)
    response = post_stream(client, "broken", a=1)
    events = sse(response.text)

    assert response.status_code == 200
    assert_stream_shape(events)
    assert printed_text(events) == "before the output fails\n"
    assert envelope_of(events) == {"error": "RuntimeError: cannot render"}


def test_function_without_prints_emits_only_start_and_result(
    client_factory, scalar, sse
):
    client = client_factory(scalar)

    events = sse(post_stream(client, "add", a=1, b=2).text)

    assert names_of(events) == ["start", "result"]


def test_function_returning_none_reports_done(client_factory, sse):
    def silent(a: int = 1) -> None:
        return None

    client = client_factory(silent)
    events = sse(post_stream(client, "silent", a=1).text)

    assert names_of(events) == ["start", "result"]
    assert envelope_of(events) == {"result": {"type": "text", "value": "Done"}}


def test_async_function_streams_and_returns(client_factory, sse):
    async def waiter(a: int = 1) -> str:
        print("from a coroutine")
        return "async done"

    client = client_factory(waiter)
    events = sse(post_stream(client, "waiter", a=1).text)

    assert names_of(events) == ["start", "print", "result"]
    assert printed_text(events) == "from a coroutine\n"
    assert envelope_of(events) == {
        "result": {"type": "text", "value": "async done"}
    }


@pytest.mark.parametrize(
    ("slug", "data"),
    [
        ("add", {"a": 1, "b": 2}),
        ("chatty", {"times": 3}),
        ("boom", {"a": 1}),
        ("chatty", {"times": "not a number"}),
    ],
)
def test_result_is_always_the_single_last_event(
    client_factory, scalar, printing, failing, sse, slug, data
):
    client = client_factory([scalar, printing, failing])

    events = sse(client.post(f"/{slug}/invoke-stream", json=data).text)

    assert_stream_shape(events)


def test_event_order_puts_prints_between_start_and_result(
    client_factory, printing, sse
):
    client = client_factory(printing)

    names = names_of(sse(post_stream(client, "chatty", times=2).text))

    assert names[0] == "start"
    assert names[-1] == "result"
    assert names.count("print") == len(names) - 2
    assert names.count("print") >= 1


def test_stream_headers_announce_an_unbuffered_event_stream(
    client_factory, scalar
):
    client = client_factory(scalar)

    response = post_stream(client, "add", a=1, b=2)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"


def test_status_is_200_when_the_work_fails(client_factory, failing):
    client = client_factory(failing)

    response = post_stream(client, "boom", a=1)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")


def test_raw_blocks_follow_the_sse_format(client_factory, printing):
    client = client_factory(printing)
    body = post_stream(client, "chatty", times=3).text

    assert body.endswith("\n\n")
    assert body.split("\n\n")[-1] == ""

    blocks = blocks_of(body)

    assert len(blocks) >= 3

    for block in blocks:
        lines = block.split("\n")

        assert lines[0].startswith("event: ")
        assert lines[0][len("event: "):].strip()
        assert len(lines) >= 2
        assert all(line.startswith("data: ") for line in lines[1:])


def test_every_event_carries_exactly_one_data_line(client_factory, sse):
    def noisy(a: int = 1) -> str:
        sys.stdout.write("a\nb\r\nc")
        print("é")
        return "line one\nline two"

    client = client_factory(noisy)
    body = post_stream(client, "noisy", a=1).text

    for block in blocks_of(body):
        assert sum(1 for line in block.split("\n")
                   if line.startswith("data: ")) == 1

    assert envelope_of(sse(body)) == {
        "result": {"type": "text", "value": "line one\nline two"}
    }


def test_stream_closes_right_after_the_result_block(
    client_factory, printing, sse
):
    client = client_factory(printing)
    body = post_stream(client, "chatty", times=2).text
    blocks = blocks_of(body)

    assert blocks[-1].startswith("event: result\n")
    assert body.endswith(blocks[-1] + "\n\n")
    assert names_of(sse(body))[-1] == "result"


def test_prints_after_the_result_are_never_emitted(client_factory, sse):
    gate = threading.Event()
    printed = threading.Event()

    def late(a: int = 1) -> str:
        def later():
            gate.wait(30)
            print("LATE MARKER")
            printed.set()

        threading.Thread(target=later, daemon=True).start()

        return "ok"

    client = client_factory(late)
    body = post_stream(client, "late", a=1).text

    gate.set()

    assert printed.wait(30)
    assert "LATE MARKER" not in body
    assert names_of(sse(body))[-1] == "result"


def test_exception_does_not_leave_the_stream_hanging(
    client_factory, failing, sse
):
    client = client_factory(failing)
    body = post_stream(client, "boom", a=1).text

    assert body.endswith("\n\n")
    assert names_of(sse(body)) == ["start", "result"]
    assert envelope_of(sse(body)) == {"error": "RuntimeError: boom"}


def test_print_events_arrive_before_the_function_returns(
    app_factory, streaming_server, sse
):
    gate = threading.Event()
    seen = {}

    def staged(a: int = 1) -> str:
        print("first")
        seen["released"] = gate.wait(30)
        print("second")
        return "ok"

    base = streaming_server(app_factory(staged))
    body = ""

    with httpx.Client(timeout=60) as client:
        with client.stream("POST", f"{base}/staged/invoke-stream",
                           json={"a": 1}) as response:
            assert response.status_code == 200

            for chunk in response.iter_text():
                body += chunk

                if "first" in body:
                    gate.set()

    events = sse(body)

    assert seen["released"] is True
    assert_stream_shape(events)
    assert printed_text(events) == "first\nsecond\n"
    assert names_of(events).count("print") >= 2


def test_disconnected_client_does_not_cancel_the_function(
    app_factory, streaming_server
):
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    seen = {}

    def blocked(a: int = 1) -> str:
        started.set()
        seen["released"] = release.wait(30)
        finished.set()
        return "released"

    base = streaming_server(app_factory(blocked))

    with httpx.Client(timeout=60) as client:
        with client.stream("POST", f"{base}/blocked/invoke-stream",
                           json={"a": 1}) as response:
            assert next(response.iter_lines()) == "event: start"

            response.close()

    assert started.wait(30)

    release.set()

    assert finished.wait(30)
    assert seen["released"] is True


def in_its_own_loop(work):
    # The suite may leave a running loop in this thread —TestClient keeps one
    # alive around its portal—, and asyncio.run() refuses to nest. A thread of
    # its own always has a free one.
    caught = {}

    def worker():
        try:
            caught["value"] = asyncio.run(work())
        except BaseException as error:
            caught["error"] = error

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(60)

    if "error" in caught:
        raise caught["error"]

    return caught["value"]


class LateCapture(PrintCapture):
    # Writes its text from inside the poll that sees the run finished, so the
    # only drain that can still find it is the one after the loop. A capture
    # that answered every drain would hide whether that last drain happens.

    def __init__(self):
        super().__init__()
        self.finished = False
        self.seeded = False

    def drain(self):
        chunks = super().drain()

        if self.finished and not self.seeded:
            self.seeded = True
            self.write("late\n")

        return chunks


def test_what_the_last_poll_did_not_see_still_travels(monkeypatch):
    capture = LateCapture()

    monkeypatch.setattr(stream_module, "PrintCapture", lambda: capture)

    def late_printer(a: int = 1) -> str:
        """Finishes after a few polls."""
        time.sleep(0.12)
        capture.finished = True
        return "done"

    async def collect():
        return [
            chunk async for chunk in stream_module._events(
                WebFunction(late_printer), {"a": 1}, True, None)
        ]

    chunks = in_its_own_loop(collect)

    printed = [chunk for chunk in chunks if chunk.startswith("event: print")]

    assert capture.seeded is True
    assert chunks[0].startswith("event: start")
    assert chunks[-1].startswith("event: result")
    assert printed == ['event: print\ndata: {"text": "late\\n"}\n\n']


def test_a_cancelled_run_is_forgotten_without_raising():
    async def cancelled():
        task = asyncio.create_task(asyncio.sleep(30))

        stream_module._running.add(task)
        task.add_done_callback(stream_module._settled)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

        await asyncio.sleep(0)

        return task

    task = in_its_own_loop(cancelled)

    assert task not in stream_module._running
