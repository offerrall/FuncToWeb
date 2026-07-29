import json
import sys
from datetime import date, time
from functools import partial
from pathlib import Path
from typing import Annotated

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from func_to_web import Description, Download, Label, Max, Min, router_of

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shared import (  # noqa: E402
    Address,
    AnyFile,
    Attachment,
    Priority,
    TxtFile,
)

__all__ = ["Address", "AnyFile", "Attachment", "Priority", "TxtFile"]


class RecordedThread:
    """Stands in for threading.Thread: it registers instead of starting.

    The sweeper is a process-wide singleton, so a real one started by the
    first router of the session would outlive its test and sweep whatever
    tmp_path came next. Tests that care about the thread read the register.
    """

    def __init__(self, registry, *, target, name=None, daemon=False):
        self.registry = registry
        self.target = target
        self.name = name
        self.daemon = daemon

    def start(self):
        self.registry.append(self)


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    import func_to_web.web.returned_files as returned_files
    import func_to_web.web.upload as upload

    uploads = tmp_path / "uploads"
    returns = tmp_path / "returns"
    uploads.mkdir()
    returns.mkdir()

    started = []

    # The attributes cover whoever never builds a router; the variables cover
    # the routers that do, which settle the directory for the process.
    monkeypatch.setenv("FUNCTOWEB_UPLOADS_DIR", str(uploads))
    monkeypatch.setenv("FUNCTOWEB_RETURNS_DIR", str(returns))
    monkeypatch.setattr(upload, "UPLOADS_DIR", uploads)
    monkeypatch.setattr(returned_files, "RETURNS_DIR", returns)
    monkeypatch.setattr(upload, "_ttl", upload.DEFAULT_TTL)
    monkeypatch.setattr(upload, "_adopted", False)
    monkeypatch.setattr(upload, "_sweeper", None)
    monkeypatch.setattr(upload, "Thread", partial(RecordedThread, started))
    monkeypatch.setattr(returned_files, "_ttl", upload.DEFAULT_TTL)
    monkeypatch.setattr(returned_files, "_adopted", False)

    return {"uploads": uploads, "returns": returns, "threads": started}


@pytest.fixture
def sweeper_threads(isolated_storage):
    return isolated_storage["threads"]


@pytest.fixture
def set_ttl(monkeypatch):
    """Set the TTL the resolver and the sweep use, as a router would."""
    import func_to_web.web.upload as upload

    def set(seconds):
        monkeypatch.setattr(upload, "_ttl", seconds)
        monkeypatch.setattr(upload, "_adopted", True)

    return set


@pytest.fixture
def set_returns_ttl(monkeypatch):
    """Set the TTL the returns sweep uses, as a router would."""
    import func_to_web.web.returned_files as returned_files

    def set(seconds):
        monkeypatch.setattr(returned_files, "_ttl", seconds)
        monkeypatch.setattr(returned_files, "_adopted", True)

    return set


@pytest.fixture
def pending_file(uploads_dir):
    """Write a pending file by hand, at any age in seconds."""
    from func_to_web.web.pending import now, pending_of

    def make(reference="a.txt", age=0, data=b"body"):
        target = uploads_dir / pending_of(reference, now() - age)
        target.write_bytes(data)
        return target

    return make


@pytest.fixture
def returned_file(returns_dir):
    """Write a stored return by hand, at any age in seconds."""
    from uuid import uuid4

    from func_to_web.web.pending import now, stamped_of
    from func_to_web.web.references import RETURNS_MARKER

    def make(filename="r.bin", age=0, data=b"body"):
        dated = stamped_of(filename, now() - age, RETURNS_MARKER)
        target = returns_dir / f"{uuid4().hex}.{dated}"
        target.write_bytes(data)
        return target

    return make


@pytest.fixture
def references_in():
    """The names of the directory, with the pending prefix stripped."""
    from func_to_web.web.pending import parsed

    def read(directory):
        names = []

        for entry in sorted(directory.iterdir()):
            found = parsed(entry.name)
            names.append(entry.name if found is None else found[1])

        return sorted(names)

    return read


@pytest.fixture
def stored_bytes(uploads_dir):
    """The bytes of a reference, whether it is promoted or still pending."""
    from func_to_web.web.pending import pending_of, stamps_of

    def read(reference):
        target = uploads_dir / reference

        if target.is_file():
            return target.read_bytes()

        stamps = stamps_of(uploads_dir, reference)

        if not stamps:
            raise FileNotFoundError(reference)

        return (uploads_dir / pending_of(reference, stamps[0])).read_bytes()

    return read


@pytest.fixture
def uploads_dir(isolated_storage):
    return isolated_storage["uploads"]


@pytest.fixture
def returns_dir(isolated_storage):
    return isolated_storage["returns"]


@pytest.fixture
def stored_file(uploads_dir):
    def make(name="a.txt", size=4, data=None):
        target = uploads_dir / name
        target.write_bytes(data if data is not None else b"x" * size)
        return name

    return make


@pytest.fixture
def sized_file(tmp_path):
    def make(name="outside.txt", size=4, data=None):
        target = tmp_path / "loose"
        target.mkdir(exist_ok=True)
        path = target / name
        path.write_bytes(data if data is not None else b"x" * size)
        return path

    return make


@pytest.fixture
def app_factory():
    def make(fns, prefix="", **options):
        app = FastAPI()
        app.include_router(router_of(fns, **options), prefix=prefix)
        return app

    return make


@pytest.fixture
def client_factory(app_factory):
    clients = []

    def make(fns, prefix="", **options):
        client = TestClient(app_factory(fns, prefix=prefix, **options))
        clients.append(client)
        return client

    yield make

    for client in clients:
        client.close()


@pytest.fixture
def scalar():
    def add(a: int, b: int = 2) -> int:
        """Add two numbers."""
        return a + b

    return add


@pytest.fixture
def failing():
    def boom(a: int = 1) -> str:
        """Always raises."""
        raise RuntimeError("boom")

    return boom


@pytest.fixture
def printing():
    def chatty(times: Annotated[int, Min(1), Max(5)] = 2) -> str:
        """Prints before returning."""
        for index in range(times):
            print(f"line {index}")
        return "done"

    return chatty


@pytest.fixture
def file_function():
    def read(document: TxtFile) -> str:
        """Reads a file."""
        return Path(document).read_text(encoding="utf-8")

    return read


@pytest.fixture
def downloading():
    def bundle(size: int = 4) -> Annotated[bytes, Download(filename="r.bin")]:
        """Returns a file."""
        return b"x" * size

    return bundle


@pytest.fixture
def nested_function():
    def complex_input(
        rows: list[Attachment],
        where: Address,
        due: date = date(2026, 8, 1),
        at: time = time(9, 30),
        priority: Priority = Priority.LOW,
        note: Annotated[str, Label("Note"), Description("Free text")] = "x",
    ) -> str:
        """Takes a nested structure."""
        return f"{len(rows)}:{where.city}:{priority.name}"

    return complex_input


@pytest.fixture
def sse():
    def parse(body):
        events = []

        for block in body.replace("\r\n", "\n").split("\n\n"):
            if not block.strip():
                continue

            name = None
            data = []

            for line in block.split("\n"):
                if line.startswith("event:"):
                    name = line[6:].strip()
                elif line.startswith("data:"):
                    data.append(line[5:])

            if name is None:
                continue

            try:
                payload = json.loads("\n".join(data))
            except json.JSONDecodeError:
                payload = None

            events.append((name, payload))

        return events

    return parse


@pytest.fixture
def plan_of_page():
    def extract(html):
        start = html.index('id="functoweb-plan"')
        opening = html.index(">", start) + 1
        closing = html.index("</script>", opening)
        return json.loads(html[opening:closing].replace("\\u003c", "<"))

    return extract


@pytest.fixture
def html_root():
    def tag(html):
        start = html.index("<html")
        return html[start:html.index(">", start) + 1]

    return tag


@pytest.fixture
def repo_root():
    return ROOT


@pytest.fixture
def local_pytypehintweb():
    candidate = ROOT.parent / "pytypehintweb"

    if not (candidate / "pyproject.toml").is_file():
        pytest.skip("pytypehintweb source checkout not available")

    return candidate


@pytest.fixture
def chrome():
    candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path("/usr/bin/google-chrome"),
        Path("/usr/bin/chromium"),
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    pytest.skip("no headless Chrome available")


@pytest.fixture
def free_port():
    import socket

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def live_server(free_port):
    import threading
    import time as clock

    import uvicorn

    servers = []

    def start(app):
        config = uvicorn.Config(app, host="127.0.0.1", port=free_port,
                                log_level="error")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        servers.append((server, thread))

        deadline = clock.monotonic() + 15

        while not server.started:
            if clock.monotonic() > deadline:
                raise RuntimeError("server did not start")
            clock.sleep(0.01)

        return f"http://127.0.0.1:{free_port}"

    yield start

    for server, thread in servers:
        server.should_exit = True
        thread.join(timeout=10)


def pytest_configure(config):
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))
