import inspect
import asyncio
import json

from fastapi.responses import StreamingResponse
from .models import FunctionMetadata
from .core.save_file_handler import cleanup_uploaded_file
from .core.print_capture import PrintCapture
from .process_result import process_result, process_error


# Can be disabled via run(stream_prints=False).
STREAM_PRINTS = True


def _run_sync_with_capture(func, cap: PrintCapture, kwargs: dict):
    """Run a sync function with stdout capture."""
    with cap.capture_sync():
        return func(**kwargs)


async def call_function(
    meta: FunctionMetadata,
    validated: dict,
    saved_paths: list[str]
) -> StreamingResponse:
    """Execute the function and stream start/print/result SSE events.

    Supports both async and sync callables. Uploaded files are always cleaned up
    after execution.
    """
    cap = PrintCapture()

    async def event_stream():
        done = asyncio.Event()
        result_holder = {}

        async def run():
            """Run the function and store the serialized result."""
            try:
                if inspect.iscoroutinefunction(meta.function):
                    with cap.capture_async():
                        result = await meta.function(**validated)
                else:
                    # Run sync functions in a thread so the event loop stays responsive.
                    result = await asyncio.to_thread(
                        _run_sync_with_capture, meta.function, cap, validated
                    )

                result_holder["data"] = {
                    "success": True,
                    **process_result(result),
                }
            except Exception as exc:
                result_holder["data"] = {
                    "success": False,
                    **process_error(exc),
                }
            finally:
                for p in saved_paths:
                    cleanup_uploaded_file(p)
                done.set()

        yield "event: start\ndata: {}\n\n"

        asyncio.create_task(run())

        # Poll captured prints while execution is still running.
        while not done.is_set():
            lines = cap.drain()
            if STREAM_PRINTS and lines:
                yield f"event: print\ndata: {json.dumps(lines)}\n\n"
            await asyncio.sleep(0.05)

        # Flush any late print output before sending the final result.
        lines = cap.drain()
        if STREAM_PRINTS and lines:
            yield f"event: print\ndata: {json.dumps(lines)}\n\n"

        yield f"event: result\ndata: {json.dumps(result_holder['data'])}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )