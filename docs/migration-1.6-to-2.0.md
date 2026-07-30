# Migrating from 1.6 to 2.0

2.0 is not just one more release: it is a different library built on the same
idea. The layers underneath change (`pytypeinput` and `pytypeinputweb` give way
to [`pytypehint`](https://github.com/offerrall/pytypehint) and `pytypehintweb`),
and **pydantic** goes with them: it is no longer involved at all. The
minimum Python version rises from 3.10 to 3.11.

Almost everything you wrote still works: the function, its type hints, its
dataclasses and its docstring. What changes is how constraints are declared, how
files are returned and which URLs the server serves.

The guide is organized by area. If you only want to migrate code, jump to
[Startup](#startup-mounting-and-the-function-space); that section plus the one on
[types](#types-constraints-and-validation) is usually enough.

## At a glance

| What breaks | Where |
| --- | --- |
| pydantic's `Field(ge=…)` → `Min`/`Max` | [types](#types-constraints-and-validation) |
| `from func_to_web.types import …` → `from func_to_web import …` | [types](#types-constraints-and-validation) |
| `Params` → a plain `@dataclass` | [types](#types-constraints-and-validation) |
| `ImageFile`, `TextFile`, … → `IsPathFile(extensions=…)` | [files](#input-files) |
| `return FileResponse(...)` → `-> Annotated[…, Download(…)]` | [results](#results-and-downloads) |
| `list[dict]` is no longer rendered as a table | [results](#results-and-downloads) |
| `create_app()` → `router_of()`, which returns an `APIRouter` | [startup](#startup-mounting-and-the-function-space) |
| `FunctionMetadata` → `WebFunction` | [startup](#startup-mounting-and-the-function-space) |
| `host` goes from `0.0.0.0` to `127.0.0.1` | [startup](#startup-mounting-and-the-function-space) |
| Every function lives at `/{slug}/`, even when it is the only one | [routes](#routes-execution-and-integration) |
| `POST /submit` multipart → `POST /{slug}/invoke` with JSON | [routes](#routes-execution-and-integration) |
| `?field=value` → `?prefill={…}` | [routes](#routes-execution-and-integration) |
| `css_vars` and the dark-mode button → `theme=` | [routes](#routes-execution-and-integration) |

And what you gain: nested dataclasses, lists of lists, unions of real types, and
defaults that are not shared between calls. Why the two layers underneath were
rewritten, and what that widened, is in
[design/history-1.6-to-2.0.md](design/history-1.6-to-2.0.md).

## Startup, mounting and the function space

`run()` keeps its job and renames most of its arguments; everything except `fns`
is keyword-only, so `run(add, "0.0.0.0", 9000)` stops working.

| 1.6 | 2.0 |
| --- | --- |
| `func` (a `list` for multi-function mode) | `fns` (any iterable) |
| `host="0.0.0.0"` | `host="127.0.0.1"`, the loopback interface only |
| `app_title` (`"Tools"` or the function name) | `title` (`"FuncToWeb"`) |
| `stream_prints=True` | `capture_prints=None` (captures regardless) |
| `max_file_size` | `max_upload_bytes` |
| `uploads_dir`, `returns_dir` | the same names, keyword-only, `str \| Path \| None` |
| `fastapi_config` | `fastapi_kwargs` |
| loose `**uvicorn_kwargs` | `uvicorn_kwargs=dict(...)`: `run(fns, log_level="debug")` becomes `run(fns, uvicorn_kwargs={"log_level": "debug"})` |
| `workers>1` and `reload=True` rejected with a `ValueError` of its own | not validated: the key reaches `uvicorn.run()`, which warns that an import string is required and ends the process with `sys.exit(1)` |

The rest of the startup surface is renamed or gone.

| 1.6 | 2.0 |
| --- | --- |
| `host.mount("/tools", create_app([add, multiply]))`, a `FastAPI` | `app.include_router(router_of([add, multiply]), prefix="/tools")`, an `APIRouter`: the prefix belongs to `include_router()` |
| `root_path` for the URLs behind a proxy | gone: every URL is relative and works under any mounted prefix |
| `FunctionMetadata(function=add, name=…, slug=…, description=…)` | `WebFunction(add, name=…, description=…, slug=…, capture_prints=…)`, the callable positional and called `fn` |
| the name prettified from `__name__`, and the slug derived from that name | `__name__` as is for both, so `name=` no longer changes the URL and `slug=` is there for that |
| any name was a slug | `doc`, `static`, `upload` and `returns` are reserved |
| a single function at `/`, several at `/{slug}` | `/{slug}/` always, trailing slash included |
| an index at `/` in either mode | only `run()` adds it: `router_of()` does not register it, and a router mounted at `/tools` returns 404 at `/tools/` |
| `css_vars`, `favicon`, `list_css_variables` | gone: appearance is controlled by `theme=` |
| `returns_lifetime` | `returns_ttl`, with `pending_ttl` for uploads |

Four keys are reserved and setting them raises `TypeError`: `title` in
`fastapi_kwargs`, and `host`, `port` and `app` in `uvicorn_kwargs`. Why `host`
and `root_path` changed is in
[design/history-1.6-to-2.0.md](design/history-1.6-to-2.0.md#defaults-that-changed-on-purpose).

→ [run.md](run.md), [router.md](router.md), [web-function.md](web-function.md)

## Types, constraints and validation

In 1.6 the constraints were pydantic's `Field(...)` on top of `pytypeinput`. In 2.0
pydantic plays no part: the catalogue is defined by `pytypehint` in atoms of its own,
which `func_to_web` re-exports, and a `Field` in the signature fails when building the
`WebFunction`. The `func_to_web.types` module no longer exists: everything comes from `func_to_web`.

### Equivalence table

| 1.6 | 2.0 | Notes |
|-----|-----|-------|
| `Field(ge=n)` / `Field(le=n)` | `Min(n)` / `Max(n)` | |
| `Field(gt=n)` / `Field(lt=n)` | `Min(n, exclusive=True)` / `Max(n, exclusive=True)` | `exclusive` is kw_only |
| `Field(min_length=n)` on `str` | `Min(n)` | Counts characters: `too short: 2 chars, minimum 3` |
| `Field(max_length=n)` on `str` | `Max(n)` | `too long: 21 chars, maximum 20`; with `exclusive` it gives `exclusive bounds are not supported for lengths` |
| `Field(min_length=)` on `list` | `Min(n)` outside the `list[...]` | `too few items: 2, minimum 3`; the constraints on the outside belong to the list and the ones on the inside to each item, as in 1.6 |
| `Field(pattern=r)` | `Pattern(r)` | `fullmatch`, not `search`: `^` and `$` are redundant and harmless, but an unanchored pattern stops accepting partial matches — `Field(pattern=r'[0-9]{5}')` accepted `'abc12345xyz'` and `Pattern('[0-9]{5}')` rejects it with **422** |
| `Field(pattern=r)` + `PatternMessage(m)` | `Pattern(r, message=m)` | `message` is kw_only |
| `Field(multiple_of=n)` | `MultipleOf(n)` | 1.6 **silently discarded it**; now it is validated. `int` only: `not a multiple of 5: 26` |
| `Literal["a", "b"]` | the same, or `Choices(values=("a", "b"))` | `Choices` is kw_only; a `Literal[str]` or `Literal[int]` left in the signature still works and validates the same way |
| `Literal[0.25, 0.5]` | `Annotated[float, Choices(values=(0.25, 0.5))]` | Regression: 1.6 accepted it and 2.0 rejects a `float` `Literal` |
| `Dropdown(fn)` | no equivalent | There are no dynamic options |
| `Enum` | `Enum` | The same in Python; over HTTP 1.6 accepted the name or the value and 2.0 accepts only the **name**: with `ADMIN = "admin"` the client sends `"ADMIN"` |
| `str \| OptionalEnabled` | `Annotated[str \| None, OptionalToggle(True)]` | The atom needs an already optional type (`OptionalToggle requires an optional field (X \| None)`) |
| `str \| OptionalDisabled` | `Annotated[str \| None, OptionalToggle(False)]` | Without the atom the toggle is decided as in 1.6: on when there is a non-null default |
| `Label`, `Description`, `Placeholder`, `Step`, `Slider`, `IsPassword`, `Rows` | same name, from `func_to_web` | Frozen dataclasses whose field is called `value`, so `Rows(count=5)` and `Label(text=…)` fail; `Step()` has no default, and `Slider` and `Choices` are kw_only |
| `Color`, `Email` | from `func_to_web` | `COLOR_PATTERN` requires 6 digits: `#f53` is no longer valid |
| `Params` | a plain `@dataclass` | `frozen=True` is no longer required, it can nest others and be optional, and it no longer flattens its fields in the form, so names no longer collide. `__post_init__` is still the place for cross-field validation, and its `ValueError` surfaces as a **422** |
| `ImageFile`, `File`, … | `IsPathFile(...)` | See the files section |

### Confirmed pitfalls

| What | What happens |
| --- | --- |
| `Slider()` on `float` | Not supported: `Float.slider is not supported yet` when building the `WebFunction`. On `int` it works, and it still requires `Min` and `Max` |
| an empty `str`, an empty `list` | 1.6 rejected both with `422` and 2.0 accepts them. If you relied on that, require it explicitly with `Min(1)` |
| `Pattern` | Only a portable subset of RegExp: `\d`, `\w`, `\s`, `\b` and the unescaped dot are rejected when building the `WebFunction`. `r'^\+?[0-9]{10,15}$'` migrates as is; `r'^\d{5}$'` does not |
| `Label` or `Description` on a list item | `field atoms cannot apply to list items`; they go on the list, and `Placeholder` does pass |
| `Extra("package.key", "value")` | The core stores it, but the web layer does not read it today: it does not appear in the plan and it changes nothing on the page |

New and with nothing to migrate from: `list[list[int]]` and unions of several
real types, whose metadata is declared per branch (`Annotated[int, Min(0)] | str`)
and whose transport is explained in the routes section.

→ [types.md](types.md)

## Input files

The type of the argument does not change: the function receives a `str` with a local
path in both versions. What changes is how the field is declared, how the file travels
and how long it lasts — in 1.6 it was `uploads_dir/<uuid>/<name>` and that folder was
deleted when the function finished; in 2.0 the file remains, ready to be reused.

### The aliases are gone

There is no `func_to_web.types`: a file field is a `str` annotated with
`IsPathFile(...)`, so `def blur(image: ImageFile)` becomes
`ImagePath = Annotated[str, IsPathFile(extensions=(".png", ".jpg"))]`. These are the
exact extensions of each alias (`pytypeinput/types.py`, `*_FILE_PATTERN`).

| 1.6 | `IsPathFile(...)` in 2.0 |
|---|---|
| `File` | `IsPathFile()` — no `extensions`, any file |
| `TextFile` | `extensions=(".txt", ".md", ".log", ".rtf")` |
| `AudioFile` | `extensions=(".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a")` |
| `DataFile` | `extensions=(".csv", ".xlsx", ".xls", ".json", ".xml", ".yaml", ".yml")` |
| `VideoFile` | `extensions=(".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".mpeg", ".mpg")` |
| `DocumentFile` | `extensions=(".pdf", ".doc", ".docx", ".odt", ".ppt", ".pptx", ".odp", ".xls", ".xlsx", ".ods")` |
| `ImageFile` | 13: `.png .jpg .jpeg .gif .webp .bmp .tiff .svg .ico .heic .avif .raw .psd` |

They are declared in lowercase and with a dot, but the comparison is
case-insensitive: a `.PNG` passes just as in 1.6.

### Transport is no longer multipart

1.6 sent everything together: `multipart/form-data` to `/submit`, with the values in a
JSON `values` field and one `UploadFile` per parameter. 2.0 splits it in two: raw bytes
go to `POST /upload` with an `X-File-Reference` header, and `POST /{slug}/invoke` then
sends that reference as an ordinary string (`{"document": "report-<uuid>.pdf"}`), so the
file is uploaded only once and re-running with a different parameter does not send it
again. A malformed reference gives `400` on `/upload`; one that does not exist gives
`422` on `/invoke`.

### Three limits, not one

| Limit | What it measures | Where it is checked | Rejection |
|---|---|---|---|
| `max_file_size` (1.6, in `run()`) | each uploaded file | while writing, in `/submit` | a form error |
| `max_upload_bytes` (2.0, in `router_of()`/`run()`) | each request to `/upload` | `POST /upload` | `413 {"detail": "uploaded file exceeds the maximum size of N bytes"}` |
| `IsPathFile(min_size=…, max_size=…)` (2.0) | the file for *that* field | `/invoke`, at build time | `422 {"error": "SchemaValueError: doc: file too large: 500 bytes, maximum 200"}` |

`max_upload_bytes` replaces `max_file_size`: a global transport ceiling. The field's
`min_size`/`max_size` are new and `/upload` does not apply them; the extension check
works the same way.

### `uploads_dir` changes shape

The name survives, and so does what it does; what changes is when it is read and how
far it reaches.

| 1.6 | 2.0 |
| --- | --- |
| a directory each `run()` used for its own uploads | keyword-only `str \| Path \| None` on `run()` and `router_of()`, defaulting to `UPLOADS_DIR` (`func_to_web.config`: `<user_data>/FuncToWeb/uploads`, via `platformdirs`), with `FUNCTOWEB_UPLOADS_DIR` when the argument is omitted |
| read when a file arrived | resolved, created and checked when the router is built, so a bad one is a `TypeError` or a `ValueError` before the server starts instead of a broken upload |
| one folder per upload, so the question did not arise | it belongs to the **process**, not to the call: [one process, one policy](router.md#one-process-one-policy) |
| the folder was deleted when the function finished | a used file stays, but an upload that no execution ever claims expires after `pending_ttl` |

`returns_dir` works the same way, with `FUNCTOWEB_RETURNS_DIR` and a default in
the system temporary directory.

### Unchanged, and one new thing

* **Optional**: same as in 1.6, `document: DocPath | None = None`.
* **Lists**: the same, `list[DocPath]`; `Min`/`Max` count files.
* **Dataclasses**: the same, at any depth, with the path to the field in the error.
* **New**: because the reference is a string, a [prefill](prefill.md) opens the
  form with the file already set (`?prefill={"document": "report-<uuid>.pdf"}`
  → `200`, with no pending upload).

→ [files.md](files.md)

## Results and downloads

In 1.6 the download was decided by the **value**: returning a `FileResponse`
turned it into a file. In 2.0 it is **declared in the return annotation** with
`Download`, and the value merely satisfies it: return a `Path`, a `str` with a path, or
`bytes`. Text, image and table are still decided by the value.

| 1.6 | 2.0 |
| --- | --- |
| `return FileResponse(data=b"…", filename="x.txt")` | `-> Annotated[bytes, Download("x.txt")]`, `return b"…"` |
| `return FileResponse(path="/tmp/report.pdf")` | `-> Annotated[Path, Download()]`, `return Path("/tmp/report.pdf")`; a bare `Download()` takes the name from the basename, as `path=` did |
| `return [FileResponse(path=…), …]` | `-> Annotated[list[Path], Download()]` |
| `return [FileResponse(data=…, filename=…), …]` | `-> Annotated[list[bytes], Download(callable)]`: with `bytes` each file needs a name of its own, so `filename` is a `(value, index) -> str` callable with the index starting at zero |
| `return None` and `return []` | the same: a `text` with `"Done"` |
| a `None` **inside** a collection | 1.6 skipped it and 2.0 emits its own `"Done"`, so `["one", None, "two"]` goes from two outputs to three |
| `return [{"name": "Ana"}, …]` or `[("Ana", 25), …]` → a table | **no longer**: it is flattened recursively, one `text` per value. `[("Ana", 25), ("Bea", 30)]` gives **4** texts, not 2 |
| `return pd.DataFrame(...)` | the same: a `table`. Only a pandas or polars `DataFrame` and a 2D numpy array are tables now |
| a PIL image, a matplotlib `Figure` | the same, both still optional dependencies; the `Figure` is closed with `pyplot.close()` and the PIL image is no longer closed |
| `return (text, image, file)` | the same, and the order is preserved |
| `GET /download/{file_id}` | `GET {prefix}/returns/{reference}`, the reference being `<identifier>.<public name>` |

Three things are now rejected when building the `WebFunction` that the
`FileResponse` used to decide at runtime: a fixed name for more than one file
(`the fixed filename 'one.txt' would name 2 files; pass a callable filename
instead`), `bytes` with no `filename`, and a return that mixes `Download` with
`OpenForm`. An exception from the function is also reported differently: it has
its row in [the responses](#the-responses).

`returns_dir` survives in the shape described for
[`uploads_dir`](#uploads_dir-changes-shape), and `returns_lifetime` is called
`returns_ttl`: a returned file stays available for `returns_ttl` and is eligible
for the sweep afterwards.

→ [outputs.md](outputs.md)

## Routes, execution and integration

### Route table

| 1.6 | 2.0 |
| --- | --- |
| `GET /` (a single function) | `GET /{slug}/` |
| `GET /{slug}` (multi-function mode) | `GET /{slug}/` |
| `POST /submit` (a single function) | `POST /{slug}/invoke` |
| `POST /{slug}/submit` (multi-function mode) | `POST /{slug}/invoke` |
| (the submit was already SSE) | `POST /{slug}/invoke-stream` |
| a multipart field inside `/submit` | `POST /upload` |
| `GET /download/{file_id}` | `GET /returns/{reference}` |
| `GET /doc` | `GET /doc` |
| `GET /_functoweb/static/styles.css` and `/scripts.js` | `GET /static/{path}`, with `ETag`; `path` accepts subdirectories (`/static/icons/alert.svg`) |
| `GET /` (index, multi-function mode) | `GET /` is added by `run()`, not by `router_of()` |

There is no special route for a single function: always `/{slug}/`, and
`/{slug}` responds `307`, which a client that does not follow redirects never
reaches. `/upload` and `/returns/{reference}` only exist if some function in the
space has a file field or returns a `Download`; otherwise, `404`. And 1.6 turned
off `/docs`, `/redoc` and `/openapi.json`, while the application built by `run()`
in 2.0 leaves them enabled: turn them off with
`fastapi_kwargs={"docs_url": None, …}`.

### The request body

1.6 sent `multipart/form-data`, with the values in a `values` field and each file
separately; 2.0 sends a **JSON** object with one key per parameter — ISO dates, an
enum by its member name, a nested dataclass, a union branch discriminated with
`$type` when needed, a file as its reference. So
`curl -X POST $URL/divide/submit -F 'values={"a": 6, "b": 3}'` becomes
`curl -X POST $URL/divide/invoke -d '{"a": 6, "b": 3}' -H 'Content-Type: application/json'`.
A multipart request gets `422`, but with FastAPI's envelope and not with the
space's `{"error": …}`: it is the body parsing that rejects it, before it reaches
the contract.

### The responses

| Case | 1.6 | 2.0 |
| --- | --- | --- |
| the function returned | `text/event-stream` with `{"success": true, "type": "text", "data": "2.0"}` | `200 {"result": {"type": "text", "value": "2.0"}}` |
| validation failed | `422 {"success": false, "errors": {"a": "Expected float, got str"}}` | `422 {"error": "SchemaTypeError: a: expected int, got str"}` |
| the function raised | `200`, inside the stream, `{"success": false, "type": "error", "data": …}` | `500 {"error": "ZeroDivisionError: division by zero"}` |

There is no `success` any more, no per-field error map (`error` is a string), and no
`data`.

### Streaming

`stream_prints=True` is renamed to `capture_prints` and is set per space
(`router_of`/`run`) and per function (`WebFunction(f, capture_prints=…)`), with the
more explicit setting winning. It now has a route of its own, so `/invoke` never
streams: `/invoke-stream` sends `start`, then zero or more `print` events and one
`result` with the same envelope as `/invoke`. Its status is always `200`, including
when the function fails, and `print` carries an object with `text`, not 1.6's list
of lines.

### Prefill by URL

| 1.6 | 2.0 |
| --- | --- |
| `/my-function?name=Alice&age=30` | `/my_function/?prefill={"name":"Alice","age":30}&hidden=["age"]` |

A prefill that is malformed, names an unknown field or carries a value that breaks
the contract gets a `400` before the page is served, instead of a half-filled form.
It can also be set from Python with `page_of()`, which requires a `WebFunction`.

### Iframe and theme

In 1.6 you added `?__embed=1` to remove the outer frame. In 2.0 it is ignored:
every page is complete and embeddable as is (`<iframe src="/tools/divide/">`),
with relative URLs and no headers that block embedding. There is no equivalent to that
cosmetic stripping.

| 1.6 | 2.0 |
| --- | --- |
| 🌙/☀️ button with `localStorage` | `theme="system"\|"light"\|"dark"` |
| `css_vars={"--functoweb-…": …}` | the `--pth-*` tokens are still there, but there is no public API that reaches them |

### With no equivalent in 1.6

* `OpenForm`: a function opens another function's form, using its return value as the
  prefill. → [open-form.md](open-form.md)
* Prefill from Python, with real values instead of URL text. → [prefill.md](prefill.md)
* `page_of()`: the HTML of a form page, without mounting any routes.
* File references reusable across calls, with no second upload.

→ [http.md](http.md), [streaming.md](streaming.md),
[sdk.md](sdk.md#embedding-a-function-page)

## Update steps

1. Upgrade to Python 3.11, install `func-to-web` 2.0 and uninstall `pytypeinput`,
   `pytypeinputweb` and, if you do not use it for anything else, `pydantic`.
2. Change the imports: everything comes from `func_to_web`, not from `func_to_web.types`.
   **Rename** `FunctionMetadata` to `WebFunction`, passing the callable positionally.
   **Replace** `OptionalEnabled` and `OptionalDisabled`, which are gone, with
   `Annotated[X | None, OptionalToggle(True)]` / `OptionalToggle(False)`.
3. Translate the `Field(...)` constraints into atoms, reviewing the regexes: the
   escapes `\d`, `\w`, `\s`, `\b` and the unescaped dot are not accepted. **Replace**
   `Literal[0.25, 0.5]` with `Annotated[float, Choices(values=(0.25, 0.5))]`.
   **Remove** the `Slider`s on `float`: they no longer build, so either make the
   field an `int` or drop the slider. `Dropdown` has no direct
   replacement: you have to **redesign the field by hand** with fixed options.
4. Turn the `Params` subclasses into plain dataclasses.
5. **Replace** the file aliases with `IsPathFile(...)` and **rename**
   `max_file_size` to `max_upload_bytes`.
6. **Move** the downloads into the return annotation with `Download`, and wrap in
   a `DataFrame` anything that used to render as a table because it was a
   `list[dict]` or a `list[tuple]`.
7. In `run()`, **rename** what still exists (`func`→`fns`,
   `app_title`→`title`, `stream_prints`→`capture_prints`,
   `fastapi_config`→`fastapi_kwargs`, and group the loose Uvicorn keys into
   `uvicorn_kwargs=`) and **remove** what does not: `css_vars` and `favicon`
   give `TypeError: run() got an unexpected keyword argument …`, and appearance
   is **redesigned by hand** with `theme=`. `uploads_dir` and `returns_dir` are
   kept as they are, and `returns_lifetime` has a counterpart again,
   `returns_ttl`.
   Decide whether you want `host="0.0.0.0"`. **Replace** `create_app()`
   with `router_of()` wherever you mount the router.
8. Update clients, links and iframes: new routes with a trailing slash, a JSON
   body at `/{slug}/invoke` and prefill with `?prefill=`.
9. Start the server and open `/doc`: it describes the published contract of the
   migrated space.

The [examples](../examples/README.md) are written against 2.0 and serve as a
template for each of these steps.
