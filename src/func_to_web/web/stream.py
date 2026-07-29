import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi.responses import StreamingResponse

from func_to_web.models.function import WebFunction
from func_to_web.models.functions import FormAction
from func_to_web.web.execution import execute
from func_to_web.web.print_capture import PrintCapture

POLL_SECONDS: float = 0.05

SSE_HEADERS: dict[str, str] = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
}

_running: set[asyncio.Task[None]] = set()


def stream(
    web_function: WebFunction,
    data: dict[str, Any],
    *,
    capture_prints: bool = True,
    form: FormAction | None = None,
) -> StreamingResponse:
    return StreamingResponse(
        _events(web_function, data, capture_prints, form),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


def _event(name: str, data: Any) -> str:
    return (
        f"event: {name}\n"
        f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    )


async def _events(
    web_function: WebFunction,
    data: dict[str, Any],
    capture_prints: bool,
    form: FormAction | None,
) -> AsyncIterator[str]:
    capture = PrintCapture() if capture_prints else None
    done = asyncio.Event()
    holder: dict[str, tuple[dict[str, Any], int]] = {}

    async def run() -> None:
        try:
            holder["response"] = await execute(web_function, data,
                                               capture=capture, form=form)
        finally:
            done.set()

    task = asyncio.create_task(run())
    _running.add(task)
    task.add_done_callback(_settled)

    yield _event("start", {})

    while not done.is_set():
        await asyncio.sleep(POLL_SECONDS)

        printed = _printed(capture)

        if printed is not None:
            yield _event("print", printed)

    printed = _printed(capture)

    if printed is not None:
        yield _event("print", printed)

    envelope, _ = holder.get(
        "response",
        ({"error": "RuntimeError: the execution produced no result"}, 500),
    )

    yield _event("result", envelope)


def _printed(capture: PrintCapture | None) -> dict[str, str] | None:
    if capture is None:
        return None

    chunks = capture.drain()

    return {"text": "".join(chunks)} if chunks else None


def _settled(task: asyncio.Task[None]) -> None:
    _running.discard(task)

    if not task.cancelled():
        task.exception()
