# HTTP API

Every function is an HTTP endpoint. Paths are relative to where the space is
mounted.

```text
POST /{slug}/invoke          run it: one request, one response
POST /{slug}/invoke-stream   the same, streaming what it prints (SSE)
POST /upload                 upload a file, when some function takes one
GET  /returns/{reference}    download a returned file
GET  /doc                    the contract of every function, in plain text
```

## `/invoke`

The body is a JSON object with one key per parameter:

```python
import requests

response = requests.post("http://127.0.0.1:8000/divide/invoke",
                         json={"a": 10, "b": 2})
payload = response.json()

if "error" in payload:
    raise RuntimeError(payload["error"])

print(payload["result"])   # {"type": "text", "value": "5.0"}
```

Values use JSON as the form sends them: a date or a time as ISO text, an enum by
its member name, a dataclass as an object, a file by its
[reference](files.md#how-a-file-travels). A missing parameter takes its default.
When a union's branches cannot be told apart by their shape, the value says
which one it is with `$type`: `{"$type": "list[str]", "$value": ["a"]}`, or a
`"$type"` key inside the object of a dataclass. Each function's plan in `/doc`
shows the exact shape.

The response has exactly one key, `result` or `error`. `result` is one
[output](outputs.md), or a list of them. The status code says whose problem it
was:

```text
200   it ran, and returned
422   the input breaks the contract   {"error": "SchemaTypeError: b: expected float, got str"}
500   the function raised             {"error": "ZeroDivisionError: float division by zero"}
```

A function can be a plain `def` or an `async def`. A plain one runs in a thread,
so a slow function does not block the server.

## Streaming

`/invoke-stream` takes the same body and sends
[server-sent events](https://developer.mozilla.org/docs/Web/API/Server-sent_events):

```text
event: start
data: {}

event: print
data: {"text": "[ 40%] file 2 of 5\n"}

event: result
data: {"result": {"type": "text", "value": "5 file(s) converted"}}
```

`print` comes zero or more times, with what the function printed since the last
one; `result` comes once, with the same envelope `/invoke` returns. The status
is always `200`, since the response has started before the function ends. This
is how the page shows a function's prints while it runs:

![The convert form showing the printed lines while it runs](images/printsse.png)

Capture is on by default. Turn it off for a whole space with
`capture_prints=False`, or for one function with
`WebFunction(fn, capture_prints=False)`. It is **experimental**: it replaces
`sys.stdout` for the rest of the process, which can conflict with a test
harness or a library that also replaces it.

If the client disconnects, the function still runs to the end.

## Files from a script

Upload the bytes first, under a reference you choose, then call the function
with that reference:

```text
POST /upload
Content-Type: application/octet-stream
X-File-Reference: report-2026.pdf

<the bytes>
```

It answers `413` past `max_upload_bytes`, `409` if the reference already exists,
and `400` if it is not a valid file name. A returned file is downloaded at
`GET /returns/{reference}`, where the reference is the `value` of its
`download` output.

## `/doc`

A plain-text document with everything a client needs: the functions, how to call
them, the outputs, and each function's full contract (types, defaults,
constraints). It is written once when the application is built, names only the
routes that exist, and writes `<base_url>` for the prefix, so an agent reads it
and knows how to call the space.

<details>
<summary>How it works inside</summary>

**Print capture.** The first function with capture that runs replaces
`sys.stdout` with a dispatcher, and it stays for the life of the process. Every
write goes to the original `stdout` and also to the execution that made it,
found by its thread or its async context, so two calls never mix their output.
Something that replaces `sys.stdout` afterwards leaves capture without effect;
something that wraps it too ends up nested with it.

**Polling.** While the function runs, the stream wakes every 50 ms to send what
is pending, so an event can be up to 50 ms late and each open stream costs that
wake-up. For internal tools with a few users, neither is noticeable.

**Static assets.** `/static/{path}` serves `page.js`, `page.css`, `sdk.js` and
the widgets of pytypehintweb, with an `ETag` and one hour of cache, so every
function of a space shares them. Every URL a page requests is relative, which is
why a space works under any prefix. The content type is fixed by extension
(`.js`, `.css`, `.svg`), because `mimetypes` reads the Windows registry, where
`.js` is often `text/plain`.

</details>
