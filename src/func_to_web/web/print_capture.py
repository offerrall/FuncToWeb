import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from queue import Empty, Queue
from threading import Lock, get_ident
from typing import Any, TextIO

_current: ContextVar["PrintCapture | None"] = ContextVar(
    "func_to_web_print_capture", default=None)

_by_thread: dict[int, "PrintCapture"] = {}

_lock = Lock()


class PrintCapture:
    def __init__(self) -> None:
        self._chunks: Queue[str] = Queue()

    def write(self, text: str) -> None:
        if text:
            self._chunks.put(text)

    def drain(self) -> list[str]:
        chunks: list[str] = []

        while True:
            try:
                chunks.append(self._chunks.get_nowait())
            except Empty:
                return chunks

    @contextmanager
    def capture_sync(self) -> Iterator[None]:
        install()

        thread = get_ident()
        previous = _by_thread.get(thread)
        _by_thread[thread] = self

        try:
            yield
        finally:
            if previous is None:
                _by_thread.pop(thread, None)
            else:
                _by_thread[thread] = previous

    @contextmanager
    def capture_async(self) -> Iterator[None]:
        install()

        token = _current.set(self)

        try:
            yield
        finally:
            _current.reset(token)


class _Dispatcher:
    def __init__(self, original: TextIO) -> None:
        self._original = original

    def write(self, text: str) -> int:
        capture = _by_thread.get(get_ident()) or _current.get()

        if capture is not None:
            capture.write(text)

        return self._original.write(text)

    def flush(self) -> None:
        self._original.flush()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._original, name)


def install() -> None:
    with _lock:
        if not isinstance(sys.stdout, _Dispatcher):
            sys.stdout = _Dispatcher(sys.stdout)
