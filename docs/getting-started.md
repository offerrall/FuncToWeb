# Getting started

## A function and its page

```python
from typing import Annotated

from func_to_web import Max, Min, run


def volume(
    width: Annotated[int, Min(1), Max(100)],
    height: Annotated[int, Min(1), Max(100)],
    depth: int = 10,
) -> float:
    """Multiply three dimensions."""
    return width * height * depth


run(volume)
```

`run()` serves it at `http://127.0.0.1:8000` until you stop it:

```text
/                 the index, one entry per function
/volume/          the form
/volume/invoke    the execution, for any HTTP client
/doc              the contract of every function, in plain text
```

The form knows that `width` and `height` go from 1 to 100 and that `depth` is 10
unless you change it; the docstring is the description on the page. The same
call from a script:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"width": 3, "height": 4}' http://127.0.0.1:8000/volume/invoke
```

```json
{"result": {"type": "text", "value": "120"}}
```

## Several functions

`run()` takes a list. `WebFunction` gives a function a name, a description or a
URL of its own:

```python
from func_to_web import WebFunction, run


def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    return a / b


run([volume, WebFunction(divide, name="Divide numbers", slug="division")],
    title="Internal tools")
```

```python
WebFunction(
    fn,
    name="",
    description="",
    slug="",
    capture_prints=None,
)
```

Left empty, `name` and `slug` come from the function's name and `description`
from its docstring. The page shows the name with `_` as spaces and its first
letter uppercased (`blur_image` reads *Blur image*). A slug is one URL segment
of letters, digits, `_` and `-`; `doc`, `static`, `upload` and `returns` are
taken by the space itself.

`WebFunctions` prepares a whole space once, to inspect it or mount it in
several applications:

```python
from func_to_web import WebFunction, WebFunctions, app_of

space = WebFunctions((WebFunction(volume), WebFunction(divide)), title="Internal tools")
app = app_of(space)
```

Both are frozen and can be read: a `WebFunction` holds its `schema`
(pytypehint's `Signature`), its `plan` (the form, as `/doc` publishes it) and its
base `html`; a `WebFunctions` holds its `functions`, its `title` and its
`document`, the text of `/doc`.

## Inside FastAPI

`app_of()` returns the same application `run()` serves, to mount wherever you
want:

```python
from fastapi import FastAPI

from func_to_web import app_of

app = FastAPI()
app.mount("/tools", app_of([volume, divide]))
```

Every route is relative, so the space works under any prefix: here the form is
at `/tools/volume/`. Authentication, middleware and CORS are the host's; see
[Security and limits](security.md).

## Options

```python
app_of(
    fns,
    *,
    title: str | None = None,
    capture_prints: bool | None = None,
    max_upload_bytes: int | None = None,
    pending_ttl: int | timedelta | None = 3600,
    returns_ttl: int | timedelta | None = 3600,
    uploads_dir: str | Path | None = None,
    returns_dir: str | Path | None = None,
    theme: Theme = "system",
) -> Starlette
```

| Option | What it sets |
| --- | --- |
| `title` | The name of the space, in the index and `/doc`. `"FuncToWeb"` if omitted. |
| `theme` | `"system"`, `"light"` or `"dark"`, for every page of the space. |
| `capture_prints` | Whether printed lines reach the page; on by default. See [HTTP API](http.md#streaming). |
| `max_upload_bytes` | The largest file `/upload` accepts. No limit if omitted. |
| `pending_ttl` | How long an upload no execution used is kept, in seconds or a `timedelta`; `None` keeps it forever. |
| `returns_ttl` | How long a file the function returned stays downloadable. |
| `uploads_dir`, `returns_dir` | Where those files are kept. Also `FUNCTOWEB_UPLOADS_DIR` and `FUNCTOWEB_RETURNS_DIR`. |

Every option is checked when the application is built, so a wrong value fails at
startup. The four storage options are one per process: the first application
that stores files decides them, and a later one asking for others gets a
warning.

`run()` takes the same options, plus the server's:

```python
run(
    fns,
    *,
    title: str | None = None,
    capture_prints: bool | None = None,
    max_upload_bytes: int | None = None,
    pending_ttl: int | timedelta | None = 3600,
    returns_ttl: int | timedelta | None = 3600,
    uploads_dir: str | Path | None = None,
    returns_dir: str | Path | None = None,
    theme: Theme = "system",
    host: str = "127.0.0.1",
    port: int = 8000,
    uvicorn_kwargs: dict[str, Any] | None = None,
) -> None
```

`uvicorn_kwargs` goes to `uvicorn.run()`, except `app`, `host` and `port`. On startup `run()` prints the installed version
(also `func_to_web.__version__`) and the two storage directories.

## Examples

Every file in [`examples/`](../examples/) runs on its own
(`python examples/basic/hello.py`) and teaches one thing:

| Folder | What it shows |
| --- | --- |
| [`basic/`](../examples/basic/) | `run()`, several functions, `WebFunction` |
| [`types/`](../examples/types/), [`validation/`](../examples/validation/) | every type and constraint |
| [`files/`](../examples/files/) | file parameters, reuse and storage |
| [`outputs/`](../examples/outputs/), [`outputs_optional/`](../examples/outputs_optional/) | text, downloads, images and tables |
| [`forms/`](../examples/forms/) | prefill, hidden fields and `OpenForm` |
| [`streaming/`](../examples/streaming/) | `print()` as progress |
| [`fastapi/`](../examples/fastapi/) | `app_of()`, `sdk.js` and modals |
| [`http/`](../examples/http/) | calling a space from a script |
| [`themes/`](../examples/themes/) | the three themes |

[`project/`](../examples/project/) holds small complete applications: a todo
list, the same list stored in a JSON file with
[pytypehintstore](https://offerrall.github.io/pytypehintstore/), users with a
photo, bookings and a gallery of outputs. Only `outputs_optional/` and
`project/gallery.py` need extra libraries (Pillow, matplotlib, pandas, polars or
numpy), and `project/todo_stored.py` needs pytypehintstore.
