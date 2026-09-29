# `sdk.js`

A few plain JavaScript functions for using a space from your own frontend:
calling a function, uploading a file, and opening a function's page in a modal.
The space serves it at `{prefix}/static/sdk.js`; there is nothing to install or
build.

```javascript
import { call, openModal } from "/tools/static/sdk.js";

const outputs = await call("/tools/divide", {a: 10, b: 2});
outputs[0].value;   // "5.0"

// A "New user" button: the form, its validation and its endpoint come from Python
openModal("/tools/create_user", {prefill: {team: "sales"}});
```

Every function takes the URL it works on: a function (`/tools/divide`) or the
space (`/tools`). There is no client to configure.

## Calling

| Function | What it does |
| --- | --- |
| `call(url, args)` | runs the function; resolves to the list of [outputs](outputs.md) |
| `callStream(url, args, {onPrint})` | the same, calling `onPrint` with what the function prints |
| `events(url, args)` | the raw stream: an async iterator of `{name, data}` events |
| `upload(spaceUrl, file, {reference})` | uploads a file and resolves to its [reference](files.md#how-a-file-travels); `reference` reuses one you already have |
| `fileReference(filename)` | mints a reference, for an upload of your own with progress |
| `downloadUrl(spaceUrl, reference)` | the URL of a returned file |
| `formUrl(spaceUrl, output)` | the URL an `OpenForm` output points to |
| `doc(spaceUrl)` | the text of `/doc` |
| `outputsOf(envelope)` | the outputs of a response you fetched yourself |

```javascript
const reference = await upload("/tools", input.files[0]);
await call("/tools/report", {source: reference});
```

`call`, `callStream`, `events`, `upload` and `doc` also take a `signal`, an
`AbortSignal` to cancel the request (the function itself still runs to the
end).

A failure throws `FuncToWebError`, with the server's message, its `status`, the
`url` and the `envelope` it received. The SDK does not validate: the server
does, and its `422` arrives as the error.

## Opening a function's page

Every function has a full page at `/{slug}/` that can be embedded in any site.
`embed()` puts it in an element of yours, and `openModal()` in a modal that
closes with `Escape`, a click outside or its button. Both take the options of
[prefill](prefill.md), spelled `prefill`, `hidden`, `autorun`, `hideTitle`,
`hideDescription` and `hideSubmit`, and `title`, the iframe's accessible name:

```javascript
embed("#panel", "/tools/add", {prefill: {a: 9}, hidden: ["a"]});

openModal("/tools/monthly_report", {autorun: true, hideSubmit: true});
```

The modal fits its content, up to 760px wide and nine tenths of the window
tall; `width`, `height`, or the CSS variables `--ftw-modal-width` and
`--ftw-modal-height` change that. `embed()` also follows its content's height;
`autoHeight: false` turns that off for both. `embed()` returns the iframe it
added; `pageUrl(url, options)` gives the page's URL with its options, for an
iframe of your own.

## Knowing what happened

```javascript
const modal = openModal("/tools/create_task", {closeOnResult: true});
const {completed, results} = await modal.closed;

if (completed) await refresh();
```

`openModal()` returns `{element, iframe, close, closed}`: `close()` closes it
from your code, and `closed` resolves when it closes by any route. `completed`
is true if a run finished, and `results` holds the outputs of the last one. `onResult`, `onError` and
`onClose` are called as it happens. `closeOnResult` is off by default, because
most results (an image, a table, a download) are meant to be read inside the
modal.

For an `embed()` or an iframe of your own, `listen(iframe, handlers)` gives the
same events: `onReady`, `onResult`, `onError`, `onNavigate` (an `OpenForm` is
moving the page) and `onResize` (the content's height). It returns `cache`, the
last `{ready, results, error}` received, and `stop()`.

<details>
<summary>How it works inside</summary>

The page posts a message to `window.parent` for each event, and nothing when it
is not embedded:

```json
{"v": 1, "kind": "result", "slug": "create_task",
 "outputs": [{"type": "text", "value": "Task 1 created"}]}
```

`kind` is `ready`, `result`, `error`, `navigate` or `resize`. A receiver ignores
a `v` or a `kind` it does not know, so a page can learn new kinds without
breaking a host. `error` means a run failed (the `error` of the envelope),
never a field the browser rejected as the user typed. `navigate` replaces
`result` when an `OpenForm` moves the page, since opening another form is not a
result. `result` carries the same outputs `call()` returns, so there is one
shape to learn.

The message goes out with a `targetOrigin` of `"*"`: the page cannot know who
embedded it, so whoever can embed a page can read its results.

</details>
