# `/doc`

`GET /doc` is the single place to discover and consume a space without reading
the Python code. It returns **plain text** (`text/plain; charset=utf-8`), not
JSON: a single text lets a person understand the space and an agent build a
call, without maintaining two representations that can drift apart.

It documents how to consume `POST /{slug}/invoke`: the body, the envelope, the
outputs, the uploads, and the downloads.

## What it contains

Three sections and nothing else:

```text
=== <space title> ===

Every path is relative to the prefix this router is mounted on; replace
<base_url> with it.

Functions:
  /<slug>  <description>

=== Calling ===

=== Plans ===

--- /<slug> ---

{ ... }
```

The header carries the space title, the notice that every path is relative to
the mounted prefix, and the function index: one slug per line with its
normalized description, in the order the functions appear in the space. A
function with no description leaves its slug alone on the line.

`Calling` covers the whole HTTP call in short prose: the body, the envelope
with its codes (`200`, `422`, and `500`), the shape of the five outputs, the
upload (`POST <base_url>/upload` with `X-File-Reference`, and its `413` and
`409` rejections), the download (`GET <base_url>/returns/<reference>`), and the
browser page. It closes by naming `invoke-stream` as the same call over SSE,
without going into the transport: that is covered in
[streaming.md](streaming.md).

## It only describes the routes that exist

`router_of()` registers `/upload` only if at least one function declares a file
parameter, and `/returns/<reference>` only if at least one function declares a
`Download`. The document follows the same rule:

```text
there are File parameters  → documents POST <base_url>/upload
there is a Download        → documents GET <base_url>/returns/<reference>
there are neither          → it does not name them
```

[`WebFunctions`](web-function.md#webfunctions) decides this while preparing the
space, in the `uploads` and `returns` fields that also govern route
registration: a single answer for both questions, so the document cannot
announce an endpoint that would answer `404`.

`Plans` is one block per function, in the same order: `--- /<slug> ---` and its
plan. There are no labeled fields around it, no `Name`, no `Web`, no `Invoke`,
because the name and the description are already in the header index and the
routes are the same for every function.

The plan is the same object that [`WebFunction`](web-function.md) holds,
serialized with indentation and without escaping non-ASCII characters. It is
not a summary: it is the complete contract the browser consumes, with the
types, the defaults, the constraints, and the labels of every parameter. That
is why it is enough to build a correct call.

## Paths are relative to the mount

The document does not know where the router is mounted, and it does not try to:
it writes `<base_url>` and tells you to replace it with the real prefix.
Mounting the space on `/tools` or on `/admin` does not change a single character
of the document.

## It is generated once

The text is composed when the space is prepared, inside
[`WebFunctions`](web-function.md#webfunctions), and stays in its `document`
field. Every request returns that same string: it is not recomputed, it is not
parameterized, and it does not depend on who asks. The one thing that does
depend on the space — which routes exist — is already resolved by the time the
text is composed. Two routers that mount the same space serve the same text.

## There is no structured API

`/doc` is not OpenAPI, nor a parallel JSON document, and no other endpoint
publishes the same thing in another format. The text is meant to be read; the
plan it carries inside is the structured part, and that is what you read to
build the call.

A host application that mounts the router also keeps its own FastAPI
`/openapi.json`, which describes the registered routes but not the type
contract of each function.

Related: [http.md](http.md), [web-function.md](web-function.md),
[router.md](router.md), [outputs.md](outputs.md).
