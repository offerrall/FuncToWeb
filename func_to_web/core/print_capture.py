import sys
import queue
import threading
import contextvars
from contextlib import contextmanager


_thread_captures: dict[int, "PrintCapture"] = {}
_async_capture: contextvars.ContextVar["PrintCapture | None"] = contextvars.ContextVar(
    "_async_capture", default=None
)
_lock = threading.Lock()
_installed = False


class _StdoutDispatcher:
    """Replaces sys.stdout once globally.
    
    Each write() checks:
      1. Thread-local capture (for sync functions in to_thread)
      2. ContextVar capture (for async functions in event loop)
      3. Falls through to original stdout
    """

    def __init__(self, original):
        self._original = original

    def write(self, text: str):
        cap = None
        tid = threading.get_ident()

        with _lock:
            cap = _thread_captures.get(tid)

        if cap is None:
            cap = _async_capture.get(None)

        if cap is not None and text.strip():
            cap._queue.put(text)

        self._original.write(text)

    def flush(self):
        self._original.flush()

    def __getattr__(self, name):
        return getattr(self._original, name)


def _ensure_installed():
    global _installed
    if not _installed:
        sys.stdout = _StdoutDispatcher(sys.stdout)
        _installed = True


class PrintCapture:
    """Thread-safe and async-safe print capture.
    
    - capture_sync():  registers by thread ID (for to_thread)
    - capture_async(): registers by ContextVar (for event loop)
    
    Usage:
        cap = PrintCapture()
        with cap.capture_sync():
            sync_function()
        
        async with cap.capture_async():
            await async_function()
        
        lines = cap.drain()
    """

    def __init__(self):
        self._queue = queue.Queue()

    def get_nowait(self) -> str | None:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def drain(self) -> list[str]:
        lines = []
        while True:
            item = self.get_nowait()
            if item is None:
                break
            lines.append(item)
        return lines

    @contextmanager
    def capture_sync(self):
        _ensure_installed()
        tid = threading.get_ident()
        with _lock:
            _thread_captures[tid] = self
        try:
            yield self
        finally:
            with _lock:
                _thread_captures.pop(tid, None)

    @contextmanager
    def capture_async(self):
        _ensure_installed()
        token = _async_capture.set(self)
        try:
            yield self
        finally:
            _async_capture.reset(token)