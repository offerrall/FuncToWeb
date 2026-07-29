# Direct HTTP

How to call a function served by FuncToWeb without a browser. Everything runs on
the standard library (`urllib.request`): these examples need no `httpx`, no
`requests` and no other extra dependency.

## Files

* `server.py` — the space the other examples call: `greet` (success), `book`
  (rejects out-of-range values), `divide` (raises `ZeroDivisionError`),
  `countdown` (prints as it runs) and `measure` (receives a file).
  `app_with_prefix()` mounts the same space under a prefix, because every route
  is relative.
* `invoke_client.py` — reads `/doc` and calls `/invoke` four times: success, an
  out-of-range argument, an exception inside the function and an extra
  argument.
* `stream_client.py` — consumes the SSE events from `/invoke-stream`.
* `upload_client.py` — uploads a temporary file to `/upload` and reuses the
  reference in two invocations, plus one with a reference that does not exist.

## Running

Terminal 1:

```bash
python examples/http/server.py
```

Terminal 2:

```bash
python examples/http/invoke_client.py
python examples/http/stream_client.py
python examples/http/upload_client.py
```

If the server is not running, each client ends with a single
`no server at http://127.0.0.1:8000: ...` line and nothing else.

Nothing here is specific to Python: the raw byte channel is what the SDKs wrap,
and from a shell `curl --data-binary` with the two headers does the same.

Status codes: `200` means the function finished, `422` that the body breaks the
input contract, and `500` that the function raised an exception.
`/invoke-stream` always answers `200`, and the error is delivered inside the
`result` event.

## Under a prefix

Mounted with `app.include_router(router_of(...), prefix="/tools")`, the routes
become `/tools/greet/invoke`, `/tools/upload` and `/tools/doc`. The clients only
need to change their `PREFIX` constant to `"/tools"`.
