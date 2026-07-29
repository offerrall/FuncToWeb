# `sdk.js`

The helpers that a frontend of your own would otherwise write by hand: calling
a function, uploading a file, following a stream, and opening a function's page
in an iframe or a modal.

It is not a Python function and there is nothing to generate: it is one more
[static asset](static-assets.md), served with the rest at
`{prefix}/static/sdk.js`.

```python
from func_to_web import router_of

app.include_router(router_of([add, divide]), prefix="/tools")
```

```javascript
import { call, openModal } from "/tools/static/sdk.js";

const outputs = await call("/tools/add", {a: 1, b: 2});

outputs[0].value;   // "3"
```

## Plain functions, no client

Every export is a function that takes the URL it works on. There is no client
to build, no state to hold, no configuration and no copy of your space to keep
in sync: the module knows the *shape* of the routes
([http.md](http.md)), nothing about your functions.

Two kinds of URL, and that is the whole convention:

```text
/tools/add    a function       call, callStream, events, pageUrl, embed, openModal
/tools        the whole space  upload, doc, downloadUrl, formUrl
```

Trailing slashes are dropped, and an absolute URL works the same
(`https://tools.example.com/add`) when the frontend and the space live on
different origins.

## Calling

```javascript
const outputs = await call("/tools/add", {a: 1, b: 2}, {signal});
```

Every call resolves to the **list of outputs**, always a list, in return order,
with the shape [outputs.md](outputs.md) describes. The single output of a
function that returns one value is `outputs[0]`.

The arguments travel in the transport format [http.md](http.md#the-input)
describes, the same one the function page sends.

## Streaming

`callStream()` is the same call over SSE ([streaming.md](streaming.md)),
resolving to the same outputs after the last event:

```javascript
const outputs = await callStream("/tools/convert", {files: 5}, {
    onPrint: (text) => log.append(text),
});
```

`onPrint` receives what the function has printed since the previous event,
which is not necessarily one line. For anything else there is `events()`, the
async generator the three event names arrive through:

```javascript
for await (const {name, data} of events("/tools/convert", {files: 5})) {
    // "start" {}, "print" {text}, "result" {result} | {error}
}
```

## Files

A file parameter travels as a reference, so the bytes go first
([files.md](files.md)). `upload()` takes the URL of the **space**, because
`/upload` belongs to the space and not to any one function:

```javascript
const reference = await upload("/tools", input.files[0]);

await call("/tools/report", {source: reference});
```

It mints the reference from the file name —the same shape the function page
uses— and returns it. `{reference}` overrides that name; the reference is
reusable, so a second call can reuse the same one without uploading again.

It uses `fetch`, so there is no upload progress. `fileReference()` is exported
precisely so that an `XMLHttpRequest` of your own can report it:

```javascript
const reference = fileReference(file.name);
const request = new XMLHttpRequest();

request.open("POST", "/tools/upload");
request.setRequestHeader("Content-Type", "application/octet-stream");
request.setRequestHeader("X-File-Reference", reference);
request.upload.addEventListener("progress", (event) => show(event.loaded));
request.send(file);
```

A `download` output is fetched at `downloadUrl("/tools", output.value)`, and a
`form` output ([open-form.md](open-form.md)) carries a relative `href` that
`formUrl("/tools", output)` turns into a URL under the space.

## Embedding a function page

Calling is not the only way to use a space from your own site: every function
has a full page at `/{slug}/` that you can open directly or embed.

```html
<iframe src="/tools/divide/" title="Divide"></iframe>
```

Responses carry no headers that prevent embedding, and the URLs the page
requests are relative, so the page works under any mounted prefix. The host
application does not rebuild the form and knows nothing about the widget
system; the iframe keeps its HTML, CSS, and JavaScript isolated. Static assets
are shared by every function on the same router, so the browser downloads them
once. The [index that `run()` adds](run.md#the-space-index) uses exactly this
mechanism: links and an iframe pointing at the pages that already exist.

Initial values do not need a channel of their own: the host application opens
the same URL with the `prefill` query parameter, and `hidden` decides which
fields are not shown. See [prefill.md](prefill.md).

That URL with its `prefill` and `hidden`, and the iframe around it, are what
every host would otherwise write by hand:

```javascript
pageUrl("/tools/add", {prefill: {a: 9}, hidden: ["a"]});

embed("#panel", "/tools/add", {prefill: {a: 9}});

const modal = openModal("/tools/divide", {
    prefill: {a: 10},
    onClose: () => refresh(),
});
```

`embed()` appends an `<iframe>` to the element you pass —an element or a CSS
selector— and returns it. `openModal()` puts that same iframe in an overlay
with a close button, closing on `Escape` and on a click outside; it returns
`{element, iframe, close}`, so the host can close it too.

Both bring their own style sheet, injected once, so they work on a page with no
CSS of its own. The overlay and its close button are the only things they
paint, and they paint them the same way always: what the user reads is the page
inside the iframe.

The theme is decided by the space, not by the host application
([router.md](router.md#theme)): a host application cannot impose its theme on
the iframe from outside, so a space that must always look dark is mounted with
`theme="dark"`.

There is still no communication back from the iframe to the host application
(result notification, height adjustment, origin policy), so a result is shown
inside the iframe and stays there.

## Failures

Everything throws `FuncToWebError`, with `status`, the `url` it called and the
`envelope` that arrived:

```javascript
try {
    await call("/tools/divide", {a: 1, b: 0});
} catch (error) {
    error.name;      // "FuncToWebError"
    error.message;   // "ZeroDivisionError: float division by zero"
    error.status;    // 500
}
```

The message is the `error` of the envelope, unchanged, and the status codes of
[http.md](http.md#the-status-code) reach the browser as they are. An answer
that is neither —FastAPI's `{"detail": ...}` on a `404`, a proxy's HTML—
becomes a `FuncToWebError` with that `detail` as its message.

`outputsOf(envelope)` is that last step on its own, for a response you fetched
yourself.

## What it is not

It does not validate. A missing argument, one that does not exist, a `Min` or a
`Pattern` are all the server's answer, and they arrive as a `422` with the
wording [http.md](http.md) publishes. The module holds no copy of your
signatures, so there is no second source of truth to drift.

It is not a form builder either: it calls, it embeds, it does not draw. The
widgets, the validation as you type and the layout stay on the function page,
which `embed()` and `openModal()` put in front of the user whole.

Related: [router.md](router.md), [http.md](http.md), [outputs.md](outputs.md),
[files.md](files.md), [streaming.md](streaming.md), [prefill.md](prefill.md),
[static-assets.md](static-assets.md), [security.md](security.md).
