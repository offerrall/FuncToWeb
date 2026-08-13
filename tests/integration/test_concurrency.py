import threading
from pathlib import Path
from typing import Annotated
from urllib.parse import parse_qs, urlparse

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

GATE_TIMEOUT = 20.0
THREAD_TIMEOUT = 60.0
PAYLOAD = 64 * 1024

SEEN_UPLOAD_DIRECTORIES: list[Path] = []


def gate_of(parties):
    return threading.Barrier(parties, timeout=GATE_TIMEOUT)


def released(gate, job):
    def start():
        gate.wait()

        return job()

    return start


def gathered(jobs):
    results = [None] * len(jobs)
    failures = []

    def runner(index, job):
        try:
            results[index] = job()
        except BaseException as error:
            failures.append(error)

    threads = [
        threading.Thread(target=runner, args=(index, job))
        for index, job in enumerate(jobs)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join(THREAD_TIMEOUT)

    assert [thread for thread in threads if thread.is_alive()] == []

    if failures:
        raise failures[0]

    return results


def paired_adder(gate):
    def add(a: int, b: int = 0) -> int:
        """Adds once both executions are in flight."""
        gate.wait()

        return a + b

    return add


def paired_failure(gate):
    def boom(a: int = 1) -> str:
        """Raises once both executions are in flight."""
        gate.wait()

        raise RuntimeError("boom")

    return boom


def alpha_printer(gate):
    def talk_alpha(lines: int = 3) -> str:
        """Prints alpha lines while the other execution prints its own."""
        gate.wait()

        for index in range(lines):
            print(f"alpha-{index}")

        gate.wait()

        return "alpha"

    return talk_alpha


def beta_printer(gate):
    def talk_beta(lines: int = 3) -> str:
        """Prints beta lines while the other execution prints its own."""
        gate.wait()

        for index in range(lines):
            print(f"beta-{index}")

        gate.wait()

        return "beta"

    return talk_beta


def shifted_adder(offset):
    def add(a: int = 0) -> int:
        """Adds a fixed offset."""
        return a + offset

    return add


def read(document: TxtFile) -> str:
    """Reads a stored file."""
    return Path(document).read_text(encoding="utf-8")


def bundle(size: int = 4096) -> Annotated[bytes, Download(filename="report.bin")]:
    """Returns a file built in memory."""
    return b"z" * size


def archive(document: TxtFile) -> Annotated[bytes, Download(filename="copy.bin")]:
    """Returns a stored file as a download."""
    return Path(document).read_bytes()


def edit_alpha(alpha: int = 0) -> str:
    """Edits the alpha space."""
    return f"alpha {alpha}"


def edit_beta(beta: int = 0) -> str:
    """Edits the beta space."""
    return f"beta {beta}"


def pick_alpha(seed: int = 1) -> Annotated[dict, OpenForm(edit_alpha)]:
    """Opens the alpha editor."""
    return {"alpha": seed * 10}


def pick_beta(seed: int = 1) -> Annotated[dict, OpenForm(edit_beta)]:
    """Opens the beta editor."""
    return {"beta": seed * 100}


def printed_text(events):
    return "".join(
        payload["text"] for name, payload in events if name == "print"
    )


def result_of(events):
    return next(payload for name, payload in events if name == "result")


def names_of(events):
    return [name for name, _ in events]


def prefill_of(envelope):
    query = parse_qs(urlparse(envelope["result"]["href"]).query)

    return query["prefill"][0]


@pytest.fixture
def gate():
    return gate_of(2)


@pytest.fixture
def clients():
    made = []

    def make(app, **options):
        client = TestClient(app, **options)
        made.append(client)

        return client

    yield make

    for client in made:
        client.close()


@pytest.fixture(autouse=True)
def no_partial_leftovers(uploads_dir, returns_dir):
    yield

    assert list(uploads_dir.glob("*.part")) == []
    assert list(returns_dir.glob("*.part")) == []


def test_two_concurrent_invocations_keep_their_own_result(client_factory, gate):
    client = client_factory(paired_adder(gate))

    first, second = gathered([
        lambda: client.post("/add/invoke", json={"a": 1, "b": 2}),
        lambda: client.post("/add/invoke", json={"a": 10, "b": 20}),
    ])

    assert first.json() == {"result": {"type": "text", "value": "3"}}
    assert second.json() == {"result": {"type": "text", "value": "30"}}


def test_two_concurrent_streams_keep_their_own_result(client_factory, gate, sse):
    client = client_factory(paired_adder(gate))

    first, second = gathered([
        lambda: client.post("/add/invoke-stream", json={"a": 1, "b": 2}),
        lambda: client.post("/add/invoke-stream", json={"a": 10, "b": 20}),
    ])

    assert (first.status_code, second.status_code) == (200, 200)
    assert names_of(sse(first.text))[0] == "start"
    assert names_of(sse(second.text))[0] == "start"
    assert result_of(sse(first.text)) == {
        "result": {"type": "text", "value": "3"}
    }
    assert result_of(sse(second.text)) == {
        "result": {"type": "text", "value": "30"}
    }


def test_concurrent_prints_never_reach_the_other_stream(
    client_factory, gate, sse
):
    client = client_factory([alpha_printer(gate), beta_printer(gate)])

    alpha, beta = gathered([
        lambda: client.post("/talk_alpha/invoke-stream", json={}),
        lambda: client.post("/talk_beta/invoke-stream", json={}),
    ])

    alpha_events = sse(alpha.text)
    beta_events = sse(beta.text)

    assert printed_text(alpha_events) == "alpha-0\nalpha-1\nalpha-2\n"
    assert printed_text(beta_events) == "beta-0\nbeta-1\nbeta-2\n"
    assert "beta" not in printed_text(alpha_events)
    assert "alpha" not in printed_text(beta_events)
    assert result_of(alpha_events) == {
        "result": {"type": "text", "value": "alpha"}
    }
    assert result_of(beta_events) == {
        "result": {"type": "text", "value": "beta"}
    }


def test_a_failing_execution_does_not_disturb_a_concurrent_one(
    client_factory, gate
):
    client = client_factory([paired_adder(gate), paired_failure(gate)])

    good, bad = gathered([
        lambda: client.post("/add/invoke", json={"a": 4, "b": 5}),
        lambda: client.post("/boom/invoke", json={}),
    ])

    assert good.status_code == 200
    assert good.json() == {"result": {"type": "text", "value": "9"}}
    assert bad.status_code == 500
    assert bad.json() == {"error": "RuntimeError: boom"}


def test_a_failing_stream_does_not_disturb_a_concurrent_one(
    client_factory, gate, sse
):
    client = client_factory([paired_adder(gate), paired_failure(gate)])

    good, bad = gathered([
        lambda: client.post("/add/invoke-stream", json={"a": 4, "b": 5}),
        lambda: client.post("/boom/invoke-stream", json={}),
    ])

    assert (good.status_code, bad.status_code) == (200, 200)
    assert result_of(sse(good.text)) == {
        "result": {"type": "text", "value": "9"}
    }
    assert result_of(sse(bad.text)) == {"error": "RuntimeError: boom"}


def test_two_concurrent_uploads_of_different_references_both_land(
    client_factory, uploads_dir, gate, references_in, stored_bytes
):
    client = client_factory(read)
    first_payload = b"A" * PAYLOAD
    second_payload = b"B" * PAYLOAD

    first, second = gathered([
        released(gate, lambda: client.post(
            "/upload",
            content=first_payload,
            headers={"X-File-Reference": "first.txt"},
        )),
        released(gate, lambda: client.post(
            "/upload",
            content=second_payload,
            headers={"X-File-Reference": "second.txt"},
        )),
    ])

    assert (first.status_code, second.status_code) == (200, 200)
    assert stored_bytes("first.txt") == first_payload
    assert stored_bytes("second.txt") == second_payload
    assert references_in(uploads_dir) == ["first.txt", "second.txt"]


def test_two_concurrent_uploads_of_one_reference_leave_one_whole_file(
    app_factory, clients, uploads_dir, gate, references_in
):
    client = clients(app_factory(read), raise_server_exceptions=False)
    first_payload = b"A" * PAYLOAD
    second_payload = b"B" * PAYLOAD

    answers = gathered([
        released(gate, lambda: client.post(
            "/upload",
            content=first_payload,
            headers={"X-File-Reference": "same.txt"},
        )),
        released(gate, lambda: client.post(
            "/upload",
            content=second_payload,
            headers={"X-File-Reference": "same.txt"},
        )),
    ])

    # The 409 usually leaves a single upload, but two that see the name free
    # both publish their own pending file: whatever is there is one payload
    # intact, never a mix, and the resolver keeps the oldest of them.
    stored = list(uploads_dir.iterdir())

    assert set(references_in(uploads_dir)) == {"same.txt"}
    assert list(uploads_dir.glob("*.part")) == []
    assert all(path.read_bytes() in (first_payload, second_payload)
               for path in stored)
    assert 200 in [answer.status_code for answer in answers]


def test_two_concurrent_downloads_are_both_served_whole(client_factory, gate):
    client = client_factory(bundle)
    references = [
        client.post("/bundle/invoke", json={"size": 4096})
        .json()["result"]["value"]
        for _ in range(2)
    ]

    first, second = gathered([
        released(gate, lambda: client.get(f"/returns/{references[0]}")),
        released(gate, lambda: client.get(f"/returns/{references[1]}")),
    ])

    assert references[0] != references[1]
    assert (first.status_code, second.status_code) == (200, 200)
    assert first.content == second.content == b"z" * 4096
    assert first.headers["content-disposition"].endswith('filename="report.bin"')


def test_each_app_of_one_app_keeps_its_own_theme(clients, scalar, html_root):
    app = FastAPI()
    app.mount("/light", app_of(scalar, theme="light"))
    app.mount("/dark", app_of(scalar, theme="dark"))
    client = clients(app)

    light, dark = gathered([
        lambda: client.get("/light/add/"),
        lambda: client.get("/dark/add/"),
    ])

    assert html_root(light.text) == '<html data-pth-theme="light">'
    assert html_root(dark.text) == '<html data-pth-theme="dark">'


def test_a_third_router_can_stay_on_the_system_theme(clients, scalar, html_root):
    app = FastAPI()
    app.mount("/light", app_of(scalar, theme="light"))
    app.mount("/plain", app_of(scalar))
    client = clients(app)

    assert html_root(client.get("/plain/add/").text) == "<html>"
    assert html_root(client.get("/light/add/").text) == (
        '<html data-pth-theme="light">'
    )


def test_two_routers_in_one_app_do_not_shadow_each_other(
    clients, scalar, printing, gate
):
    app = FastAPI()
    app.mount("/first", app_of(scalar, title="Adders"))
    app.mount("/second", app_of(printing, title="Chatters"))
    client = clients(app)

    first, second = gathered([
        released(gate, lambda: client.post("/first/add/invoke", json={"a": 1})),
        released(gate, lambda: client.post(
            "/second/chatty/invoke", json={"times": 1}
        )),
    ])

    assert first.json() == {"result": {"type": "text", "value": "3"}}
    assert second.json() == {"result": {"type": "text", "value": "done"}}
    assert client.post("/first/chatty/invoke", json={}).status_code == 404
    assert client.post("/second/add/invoke", json={"a": 1}).status_code == 404
    assert client.get("/first/doc").text.startswith("=== Adders ===")
    assert client.get("/second/doc").text.startswith("=== Chatters ===")


def test_two_spaces_can_serve_the_same_slug(clients, gate):
    app = FastAPI()
    app.mount("/first", app_of(shifted_adder(1)))
    app.mount("/second", app_of(shifted_adder(1000)))
    client = clients(app)

    first, second = gathered([
        released(gate, lambda: client.post("/first/add/invoke", json={"a": 5})),
        released(gate, lambda: client.post("/second/add/invoke", json={"a": 5})),
    ])

    assert first.json() == {"result": {"type": "text", "value": "6"}}
    assert second.json() == {"result": {"type": "text", "value": "1005"}}


def test_an_open_form_resolves_inside_its_own_space(clients, gate):
    app = FastAPI()
    app.mount("/first", app_of([
        WebFunction(pick_alpha, slug="pick"),
        WebFunction(edit_alpha, slug="edit"),
    ]))
    app.mount("/second", app_of([
        WebFunction(pick_beta, slug="pick"),
        WebFunction(edit_beta, slug="edit"),
    ]))
    client = clients(app)

    first, second = gathered([
        released(gate, lambda: client.post("/first/pick/invoke", json={"seed": 2})),
        released(gate, lambda: client.post("/second/pick/invoke", json={"seed": 2})),
    ])

    alpha_prefill = prefill_of(first.json())
    beta_prefill = prefill_of(second.json())

    assert first.json()["result"]["href"].startswith("../edit/?")
    assert second.json()["result"]["href"].startswith("../edit/?")
    assert alpha_prefill != beta_prefill
    assert client.get("/first/edit/", params={"prefill": alpha_prefill}).status_code == 200
    assert client.get("/second/edit/", params={"prefill": beta_prefill}).status_code == 200
    assert client.get("/second/edit/", params={"prefill": alpha_prefill}).status_code == 400
    assert client.get("/first/edit/", params={"prefill": beta_prefill}).status_code == 400


def test_an_open_form_target_of_one_space_is_unknown_to_the_other(clients):
    app = FastAPI()
    app.mount("/first", app_of([
        WebFunction(pick_alpha, slug="pick"),
        WebFunction(edit_alpha, slug="edit"),
    ]))
    app.mount("/second", app_of([
        WebFunction(pick_beta, slug="pick"),
        WebFunction(edit_beta, slug="edit"),
    ]))
    client = clients(app)

    assert client.post("/first/edit/invoke", json={"alpha": 5}).json() == {
        "result": {"type": "text", "value": "alpha 5"}
    }
    assert client.post("/second/edit/invoke", json={"beta": 5}).json() == {
        "result": {"type": "text", "value": "beta 5"}
    }
    assert client.post("/first/edit/invoke", json={"beta": 5}).status_code == 422
    assert client.post("/second/edit/invoke", json={"alpha": 5}).status_code == 422


def test_temporary_storage_starts_empty_and_gets_dirtied(
    uploads_dir, returns_dir
):
    assert list(uploads_dir.iterdir()) == []
    assert list(returns_dir.iterdir()) == []

    SEEN_UPLOAD_DIRECTORIES.append(uploads_dir)
    (uploads_dir / "leftover.txt").write_bytes(b"x")
    (returns_dir / "leftover.bin").write_bytes(b"x")


def test_temporary_storage_is_a_fresh_directory_for_the_next_test(
    uploads_dir, returns_dir
):
    assert list(uploads_dir.iterdir()) == []
    assert list(returns_dir.iterdir()) == []
    assert SEEN_UPLOAD_DIRECTORIES
    assert uploads_dir not in SEEN_UPLOAD_DIRECTORIES


def test_a_burst_of_concurrent_work_leaves_no_partial_file(
    client_factory, uploads_dir, returns_dir
):
    client = client_factory(archive)
    references = [f"burst-{index}.txt" for index in range(4)]
    gate = gate_of(len(references))

    uploads = gathered([
        released(gate, lambda reference=reference: client.post(
            "/upload",
            content=reference.encode("utf-8") * 128,
            headers={"X-File-Reference": reference},
        ))
        for reference in references
    ])

    download_gate = gate_of(len(references))

    downloads = gathered([
        released(download_gate, lambda reference=reference: client.post(
            "/archive/invoke", json={"document": reference}
        ))
        for reference in references
    ])

    stored = [answer.json()["result"]["value"] for answer in downloads]

    fetch_gate = gate_of(len(stored))

    fetched = gathered([
        released(fetch_gate, lambda reference=reference: client.get(
            f"/returns/{reference}"
        ))
        for reference in stored
    ])

    assert [answer.status_code for answer in uploads] == [200] * len(references)
    assert [answer.status_code for answer in fetched] == [200] * len(references)
    assert {answer.content for answer in fetched} == {
        reference.encode("utf-8") * 128 for reference in references
    }
    assert list(uploads_dir.glob("*.part")) == []
    assert list(returns_dir.glob("*.part")) == []
    assert len(set(stored)) == len(stored)
