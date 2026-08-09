# `sdk.js`

The helpers that a frontend of your own would otherwise write by hand: calling
a function, uploading a file, following a stream, opening a function's page in
an iframe or a modal, and hearing what happened inside it.

It is not a Python function and there is nothing to generate: it is one more
[static asset](static-assets.md), served with the rest at
`{prefix}/static/sdk.js`.

```python
from func_to_web import app_of

app.mount("/tools", app_of([add, divide]))
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

`listen()` is the one export that takes no URL: it takes an `<iframe>` you
already have, because what it works on is a page that is already open.

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
are shared by every function on the same application, so the browser downloads them
once. The [index that `run()` adds](run.md#the-space-index) uses exactly this
mechanism: links and an iframe pointing at the pages that already exist.

Initial values do not need a channel of their own: the host application opens
the same URL with the `prefill` query parameter, `hidden` decides which fields
are not shown, and `autorun` asks the page to submit itself once it is ready.
See [prefill.md](prefill.md).

That URL with its three parameters, and the iframe around it, are what every
host would otherwise write by hand:

```javascript
pageUrl("/tools/add", {prefill: {a: 9}, hidden: ["a"]});

embed("#panel", "/tools/add", {prefill: {a: 9}});

const modal = openModal("/tools/divide", {
    prefill: {a: 10},
    onClose: () => refresh(),
});

// A modal opened for its answer: no form to fill, so no button to press
openModal("/tools/monthly_report", {autorun: true});
```

`autorun` is for the modal you open to *see* something —a report, a chart, a
generated file, a link— rather than to fill anything in. `call()` would skip
the button too, but it hands you JSON and leaves you to draw the table, the
image or the download; opening the page is how you get those drawn for you.
The page presses its own button and nothing else changes: same validation,
same uploads, same stream, same [announcements](#reacting-to-the-modal). A
form that is missing a value is left untouched and waits for a click.

`embed()` appends an `<iframe>` to the element you pass —an element or a CSS
selector— and returns it. `openModal()` puts that same iframe in an overlay
with a close button, closing on `Escape` and on a click outside; it returns
`{element, iframe, close, closed}`, so the host can close it too and can wait
for it.

Both bring their own style sheet, injected once, so they work on a page with no
CSS of its own. The overlay and its close button are the only things they
paint, and they paint them the same way always: what the user reads is the page
inside the iframe.

### The size of a modal

A modal is **760px wide and nine tenths of the window tall** by default,
because the thing inside it is a form and a form that does not fit is a form
with a scrollbar over it. Height is the axis that matters —a form grows
downwards— so it is the one that follows the screen instead of a fixed number.

Two ways to change it, and they are the same way twice:

```javascript
openModal("/tools/create_user", {height: "100%", width: 1100});
```

```css
:root {
    --ftw-modal-width: 1100px;
    --ftw-modal-height: 100%;
}
```

The option sets those variables on that one panel; the CSS sets them for every
modal. Both take any CSS length —`px`, `%`, `vh`, `rem`, a `calc()`— and the
option also takes a plain number, read as pixels. Anything else raises
`FuncToWebError: the height must be a number of pixels or a CSS length`.

Whatever is asked for, the panel is capped at the window:

```text
width:  min(--ftw-modal-width,  100%)
height: min(--ftw-modal-height, 100%)
```

So no setting can push a corner of the modal off screen, and `100%` is the
ceiling rather than an overflow. That ceiling is the window **minus the 48px
the overlay keeps** around the panel, which is what makes it read as a modal
and not as a page.

A form taller than that scrolls inside the iframe, and no height setting
changes it: the iframe does not grow to fit its content, since the page does
not report a height. What the default guarantees is the other half of the
problem — that nothing above the form is wasted.

The theme is decided by the space, not by the host application
([router.md](router.md#theme)): a host application cannot impose its theme on
the iframe from outside, so a space that must always look dark is mounted with
`theme="dark"`.

## Reacting to the modal

A modal that only opens is half a feature: the host that opens *create task*
wants to refresh its list afterwards, and only if something was really created.
The page announces what happens inside it, and the handle is where you wait for
it:

```javascript
const modal = openModal("/tools/create_task", {closeOnResult: true});

const {completed, results} = await modal.closed;

if (completed) await refresh();
```

`closed` resolves **once**, when the modal closes by any route —the close
button, a click outside, `Escape`, `closeOnResult`, your own `close()`— with two
values:

```text
completed   true if at least one run finished inside the modal
results     the outputs of the last run, or null if there were none
```

A modal the user dismisses without running anything resolves
`{completed: false, results: null}`, which is the same shape and needs no
special case. `results` is the list of outputs [outputs.md](outputs.md)
describes, exactly the one `call()` resolves to.

Three options tell the modal what to do as it happens:

```javascript
openModal("/tools/create_task", {
    closeOnResult: true,
    onResult: (outputs) => toast(outputs[0].value),
    onError: (message) => toast(message),
    onClose: () => release(),
});
```

`closeOnResult` defaults to **`false`**: a result is drawn *inside* the page —an
image, a table, a download link— and closing the modal would throw away what
the user came to see. Turn it on for a form whose result is a confirmation, like
the one above, and leave it off for anything the user has to read.

### Your own iframe

`embed()`, or an `<iframe>` you wrote yourself, hears the same announcements
through `listen()`:

```javascript
const frame = embed("#panel", "/tools/create_task");

const channel = listen(frame, {
    onReady: () => spinner.hide(),
    onResult: (outputs) => refresh(),
    onError: (message) => show(message),
    onNavigate: (href) => track(href),
});

channel.cache;   // {ready, results, error}, the last of each
channel.stop();  // stops listening
```

Every handler is optional. `cache` is what has arrived so far, for a host that
prefers to read rather than be called, and `openModal()` is built on exactly
this: `closed` reports that cache when the overlay goes away.

### The protocol

The page posts one message per event to `window.parent`, and nothing at all
when it is not embedded. Four kinds, each with the payload it needs:

```text
ready                        the page is up and the form is mounted
result    {outputs}          a run finished; the outputs it just drew
error     {message}          a run failed; the error of the envelope
navigate  {href}             an OpenForm result is about to move the iframe
```

Every message also carries `v`, the protocol version, and `slug`, the function
it comes from:

```json
{"v": 1, "kind": "result", "slug": "create_task",
 "outputs": [{"type": "text", "value": "Task 1 created"}]}
```

`v` is how this can grow without breaking a host: a receiver ignores, in
silence, anything whose `v` it does not know, anything with no `kind`, and any
`kind` it has not heard of. `listen()` does that for you, so a host written
today keeps working against a page that learns a fifth kind tomorrow.

Two boundaries are deliberate. `error` is a *run* that failed —the `error` of
the envelope, a `422` or a `500` ([http.md](http.md#the-status-code))— and never
a field the browser rejected as you typed: that is not the host's business, and
one kind means one thing. And `navigate` is emitted **instead of** `result` on
the [OpenForm](open-form.md) branch, because moving to another form is not a
result and must not count as one.

`result` can arrive more than once: the user changes a value and runs again.
Each arrival replaces the previous one, which is why `results` is the *last*
run and not a list of runs.

The message is posted with a `targetOrigin` of `"*"`, because the page does not
know who embedded it: whoever can embed a page can read what runs inside it. See
[security.md](security.md#the-result-travels-to-whoever-embeds-the-page).

Still missing, and not part of this: adjusting the iframe's height to its
content, and any host-to-page direction. Initial values still travel as
`prefill` in the URL ([prefill.md](prefill.md)), not as a message.

Why the autoclose is off, why `error` skips validation and why `result` reuses
the envelope: [design/sdk.md](design/sdk.md).

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
