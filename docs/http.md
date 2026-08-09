# Execution over HTTP

`POST /{slug}/invoke` runs a function and returns its result or its error. It is
**the** execution endpoint, and the recommended one for scripts, services,
applications and agents: one request, one response.

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/create_tag/invoke",
    json={"name": "demo"},
)

payload = response.json()

if "error" in payload:
    raise RuntimeError(payload["error"])

print(payload["result"])
```

The web interface also uses `POST /{slug}/invoke-stream`, which streams what the
function prints while it runs and ends with this same envelope. A programmatic
client does not need it; see [streaming.md](streaming.md).

## The input

```text
POST /{slug}/invoke
Content-Type: application/json
```

The body is always a **JSON object** with one key per parameter, in the
browser's transport format:

* dates and times, as ISO text;
* an enum, the name of its member;
* a dataclass, a nested object;
* a union branch, discriminated with `$type` when the transport needs it and
  cannot guess;
* a file, the reference that names it (see [files.md](files.md)).

This is the same format that the function's plan describes and that URL
[prefill](prefill.md) uses.

That object goes through two stages before it reaches the function: `decode()`
interprets the transport, and `schema.build()` validates and builds the
arguments. Inside `decode()`, every file reference is replaced by the local path
of the stored file.

The function receives real Python values, not the JSON or an approximation of
it. Parameters that are absent take their default; a parameter that is missing
and has no default, or one that does not belong to the signature, is a contract
error.

## The response

```json
{"result": {"type": "text", "value": "Hola"}}
```

```json
{"error": "<ExceptionType>: <message>"}
```

Exactly one of the two keys, never both. A client reads `result` by the presence
of the key, not by its value. The function finishing does not guarantee
`result`: if its return value breaks what it declares, or cannot be converted
into outputs, the response carries `error` even though the function raised
nothing.

`result` carries one output, or a list of outputs in the order the function
returned them. The types, and the value each one produces, are described in
[outputs.md](outputs.md). Since every output is converted to text before it is
sent, serialization does not depend on the type the function returns, and the
bytes of a download never travel in the JSON: they are served separately,
through their reference.

The envelope is identical for both endpoints: what `/invoke` returns as its body
is exactly what `/invoke-stream` sends in its `result` event.

## The status code

The envelope says **what** happened; the status code says **whose** problem it
is.

```text
200   the function finished and its return became outputs
422   the body does not meet the input contract
500   the function raised an exception, or its return breaks what it declares
```

```text
422  {"error": "SchemaTypeError: when: expected date, got str"}
422  {"error": "SchemaTypeError: missing argument(s): at, contact"}
422  {"error": "SchemaTypeError: unexpected argument(s): zzz"}
422  {"error": "FileNotFoundError: File not found: nope.pdf"}
500  {"error": "ZeroDivisionError: float division by zero"}
500  {"error": "ReturnContractError: expected bytes for Download, got Path"}
```

The `422` covers everything that fails **before** entering the function: the
transport, the decoding, the construction of the arguments and the resolution of
a file reference. The `500` covers everything that fails inside it or after it.

A client that reads only the body is unaffected; the status code is there so
that a proxy, a log or a dashboard can tell a malformed request apart from a
server failure.

On `/invoke-stream` the status code is always `200`: the response has already
started by the time the function fails.

## The edge outside the envelope

A body that is not a JSON object (a list, a number, text or nothing at all)
gets `422 {"detail": "body must be valid JSON"}` or
`422 {"detail": "body must be a JSON object"}`. This happens before the
request reaches the function. A client that reads `result`/`error` has to
account for it.

Related: [outputs.md](outputs.md), [streaming.md](streaming.md),
[files.md](files.md), [api-docs.md](api-docs.md), [types.md](types.md).
