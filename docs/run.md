# `run()`

Starts the standalone application: it prepares the space, mounts the router at
the root, adds the index at `/` and starts Uvicorn.

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
    fastapi_kwargs: dict[str, Any] | None = None,
    uvicorn_kwargs: dict[str, Any] | None = None,
) -> None
```

```python
from func_to_web import run


run([add, divide], title="Internal tools")
```

It accepts exactly the same input as [`router_of()`](router.md), with the same
errors, and `capture_prints`, `max_upload_bytes`, `pending_ttl`, `returns_ttl`,
`uploads_dir`, `returns_dir` and `theme` are passed on unchanged to the router,
which validates them all before Uvicorn starts. `title`, `host` and `port` are
the three it handles itself: by default the server listens on `127.0.0.1:8000`.
The `theme` also applies to the index, which shares the space with the pages it
frames.

`FUNCTOWEB_UPLOADS_DIR` and `FUNCTOWEB_RETURNS_DIR` say from outside the code
what `uploads_dir` and `returns_dir` say in it, which is the usual place for a
deployment to say it:

```python
run(functions, uploads_dir="/srv/functoweb/uploads")
```

Which two directories were in force is not left to be guessed: `run()`
announces them, with the version, on the line before the server starts.

```text
FuncToWeb 2.0.0
UPLOADS DIR: /srv/functoweb/uploads
RETURNS DIR: /tmp/FuncToWeb/returns
```

The call blocks until the server stops, and returns nothing.

```text
router_of() = integration
run()       = minimal standalone application
```

A real integration does not go through here: when you already have a host
application with its own authentication, routes and deployment, what you mount
is the router.

## What it builds

A FastAPI application with the space title, the router mounted with no prefix,
and one extra route, the index:

```text
/                       index of the registered functions
/{slug}/                the page of each function
/{slug}/invoke          its execution
/{slug}/invoke-stream   the same execution, streamed over SSE
/doc                    the space document
/static/{path}          the shared assets
/upload                 only if some function has a file field
/returns/{ref}          only if some function declares a Download
```

The last two are conditional: they appear only if some function needs them.
Every route except the index is registered by the router, and
[router.md](router.md) covers them all in detail. The index is the only thing
`run()` adds on top of `router_of()`.

## FastAPI and Uvicorn options

`fastapi_kwargs` is passed to `FastAPI(...)` and `uvicorn_kwargs` to
`uvicorn.run(...)`. Both are copied before use, so the caller's dictionaries are
never modified.

```python
run(
    divide,
    fastapi_kwargs={"docs_url": None},
    uvicorn_kwargs={"log_level": "debug"},
)
```

Some keys are reserved because they are already explicit arguments; setting them
raises `TypeError` instead of being silently ignored:

```text
TypeError: fastapi_kwargs cannot contain 'title'; use the title argument
TypeError: uvicorn_kwargs cannot contain 'host'; use the host argument
TypeError: uvicorn_kwargs cannot contain 'port'; use the port argument
TypeError: uvicorn_kwargs cannot contain 'app'; run() builds it internally
```

## The space index

The page `run()` adds at `/` is deliberately minimal: one link per function, in
space order, with the `name` and the `description` its
[`WebFunction`](web-function.md) already carries.

```html
<a href="#add" data-slug="add"><strong>Add</strong><span>Add two numbers.</span></a>
<a href="#division" data-slug="division"><strong>Divide numbers</strong></a>
```

With no description there is no `<span>`: no text is invented and no gap is
left. Both values are escaped, and the space `title` is the `<title>` of the
page and the heading of the sidebar. The name is formatted the same way as on
the function page (`_` becomes spaces and the first letter is capitalized), so
`add` in the example reads as `Add`. See
[web-function.md](web-function.md#the-name-is-formatted-when-it-is-displayed).

The selection lives in the URL hash, which is the function slug, and that is why
each function is linkable:

```text
/#add        opens /add/
/#division   opens /division/
```

An empty or unknown hash opens the first function instead of leaving the page
blank, and the chosen one opens in an `<iframe>` that only navigates
same-origin pages. Why it navigates with `location.replace()`, and why the
index carries no form logic of its own, is in [design/run.md](design/run.md).

`/doc` appears as another entry in the sidebar, with no `data-slug` and opening
in a new tab.

The HTML is composed at startup, with the space already prepared, and every
request to `/` returns the same text from memory.

Related: [router.md](router.md), [getting-started.md](getting-started.md),
[web-function.md](web-function.md), [sdk.md](sdk.md#embedding-a-function-page).
