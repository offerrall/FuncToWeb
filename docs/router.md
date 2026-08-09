# `app_of()`

Turns a space of functions into a Starlette application that can be mounted by
a compatible ASGI host.

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

```python
from fastapi import FastAPI

from func_to_web import app_of


app = FastAPI()
app.mount("/tools", app_of([add, divide]))
```

The prefix belongs to `mount()`: all routes are relative, so the space works
under any mounted prefix.

## What it accepts

`fns` is the space, in any of its forms: a function, a
[`WebFunction`](web-function.md), an iterable mixing both (list, tuple,
generator), or an already prepared
[`WebFunctions`](web-function.md#webfunctions).

Plain functions are wrapped in a `WebFunction`, which derives their name,
description and slug; a `WebFunction` is taken as it is. The order of the
iterable is preserved: it is the order of `/doc` and of the index.

| Input | Error |
| --- | --- |
| `[]` | `ValueError: at least one function is required` |
| `None`, `3`, `"add"`, `{"a": add}` | `TypeError: entries must be callables or WebFunction instances` |
| `[add, 3]` | the same `TypeError` |
| two entries with the same slug | `ValueError: two functions share the slug 'add'` |
| a function no slug can be derived from | `ValueError: cannot derive a valid slug…` |

A `str` and a `dict` are iterables, so they do get traversed; their elements —
characters or keys — are not functions, and the error is the same `TypeError`.
Errors in the definition itself are those of
[`WebFunction`](web-function.md), which is built here.

## What routes it registers

```text
GET  /{slug}/                the page of the function
POST /{slug}/invoke          its execution
POST /{slug}/invoke-stream   the same execution, streamed over SSE
GET  /doc                    the document of the space
GET  /static/{path}          the shared assets
POST /upload                 only if some function has a file field
GET  /returns/{ref}          only if some function declares a Download
GET  /                       index of the registered functions
```

Six of them are always there, the index at `/` among them; `invoke-stream` also
exists for functions that print nothing. `/upload` and `/returns` are registered
only when some function needs them, so a space without input files does not
expose `/upload`, and one without output files does not expose `/returns`. That
is why four slugs are reserved: `doc`, `static`, `upload` and `returns`. All
four are always rejected, even in a space that registers neither of the two
conditional routes:

```python
app_of([WebFunction(add, slug="upload")])
# ValueError: slug 'upload' is reserved
```

See [http.md](http.md), [streaming.md](streaming.md),
[api-docs.md](api-docs.md), [static-assets.md](static-assets.md),
[files.md](files.md) and [outputs.md](outputs.md).

## The arguments

`title` names the space in `/doc` and in the index. If you do not set it, the
title is `"FuncToWeb"`; whatever you pass is normalized with `strip()`. An
already prepared `WebFunctions` carries its own title, so passing a title again
is an error:

```python
app_of(space, title="Other")
# TypeError: the prepared space already carries its title;
# set the title when creating WebFunctions
```

`capture_prints` decides, for the whole space, whether what the functions print
is streamed over [`/invoke-stream`](streaming.md). If you do not set it, output
is captured; a value declared by a `WebFunction` overrides it.

`max_upload_bytes` is the maximum size, in bytes, of each file accepted by the
`/upload` route of this application. If you do not set it, FuncToWeb imposes no
limit. It is validated when the application is built. See [files.md](files.md).

`pending_ttl` is how long an uploaded file survives without being used: an
upload nothing ever [promotes](files.md#pending-and-promoted-files) is deleted
once it is older than this. It takes seconds as an `int` or a
`datetime.timedelta`, and `None` turns the whole cycle off, so `/upload`
publishes definitively.

`returns_ttl` is the same setting for the other direction: how long a file the
function returned survives in the returns directory before it is deleted. It
is simpler, because there is nothing to promote — a download is fetched or it
is not, and neither makes it permanent, so there is one state and one date.
With `None` there is no date in the name of the returned file either.

Both take the same values, are validated when the application is built, like the
limit, and raise the same two errors, each with its own name in them:

| Value | What it means for either setting |
| --- | --- |
| `3600` | the default: one hour |
| `timedelta(days=1)` | normalized to seconds |
| `None` | no expiry, and no sweeping of that directory |

```text
TypeError: pending_ttl must be int, timedelta or None
ValueError: pending_ttl must be greater than zero
```

They are two settings, not one, so a space can hold its uploads for a week and
still hand out downloads that live an hour. Why both default to one hour is in
[design/router.md](design/router.md).

`uploads_dir` and `returns_dir` say where each of those two directories is.
Neither is required: uploads go to the user's data directory of the platform
(`%LOCALAPPDATA%`, `~/Library/Application Support` or `$XDG_DATA_HOME`) and
returned files to a folder of their own inside the system temporary directory. Both can also be set from outside the code, which is what a
deployment usually wants:

```text
FUNCTOWEB_UPLOADS_DIR    where the uploaded files are stored
FUNCTOWEB_RETURNS_DIR    where the returned files are stored
```

The argument wins over the variable, and the variable over the default, so
naming a directory in the call means it and leaving it out lets the
environment decide:

```python
app_of(functions, uploads_dir="/srv/functoweb/uploads")
```

Whichever of the three wins is checked when the application is built: it is made
absolute, it is created if it is missing, and whatever stops that from
happening —a permission, a full disk, a name already taken by a file— is
raised there. The first request never meets a directory this process cannot
write to.

```text
TypeError: uploads_dir must be str, Path or None
ValueError: returns_dir is not a directory: /etc/hosts
```

A relative path is resolved against the working directory of the process,
which is not where the code lives; an absolute one is the honest way to write
it. And the two directories are independent: moving the uploads says nothing
about the returns.

### One process, one policy

One process is one storage directory, so it is one policy: what the first
application settles governs everything afterwards —where `/upload` publishes, what
the resolver expires and what the single sweeping thread deletes in either
directory— for every space mounted in that process.

| Settled by | Settings |
| --- | --- |
| the first application with file fields | `uploads_dir` and `pending_ttl` |
| the first application with a `Download` | `returns_dir` and `returns_ttl` |

A later application asking for a different one does not get it, and is told so
rather than left guessing:

```python
app_of(reports, pending_ttl=3600)
app_of(invoices, pending_ttl=None)
# UserWarning: pending_ttl=None is ignored: this process already stores its
# files with pending_ttl=3600, settled by an earlier application. Storage is one
# policy per process, not one per application.
```

The warning reads the same for `returns_ttl`, for `uploads_dir` and for
`returns_dir`, with the name of the setting changed: it is one sentence for
every storage setting, not one per setting. Two different directories need
two processes, exactly as two TTLs do, because the `409`, the promotion and
the sweep all work on what the process settled. See
[files.md](files.md#pending-and-promoted-files),
[outputs.md](outputs.md#where-the-files-live) and
[limitations.md](limitations.md).

## Theme

`theme` decides how every page of the space looks. There are exactly three
values:

```text
"system"   follows the operating system preference   (default)
"light"    light, always
"dark"     dark, always
```

There is no coercion: `"Dark"`, `"auto"`, `"light "`, `None` or a `bool` fail
when the application is built, not on the first request.

```python
app_of([add, divide], theme="Dark")
# ValueError: theme must be one of system, light, dark; got 'Dark'

app_of([add, divide], theme=None)
# TypeError: theme must be str
```

What it does is write the attribute on the `<html>` element the server serves:

```html
<html>                        theme="system"
<html data-pth-theme="light"> theme="light"
<html data-pth-theme="dark">  theme="dark"
```

It goes in the initial markup, so the theme is resolved before the first paint
and **there is no flicker**.

The theme belongs to the **space**, not to each function: all of its pages share
a single theme, and opening a form with `prefill` or `hidden` preserves it. Two
themes need two applications.

See [static-assets.md](static-assets.md#theme) and
[design/router.md](design/router.md).

## Everything is prepared when the application is built

Each entry compiles its metadata, its schema, its plan and its base HTML at that
point, not per request. An inconsistent definition fails at startup, before the
first request is accepted. Building the application does not call any function: it
only reads their signatures.

## What it does not do

* It does not create the application or start a server: that is [`run()`](run.md).
* It does not decide the mounted prefix.
* It does not provide authentication, middleware or CORS: whatever applies comes
  from the host application. See [security.md](security.md).

Related: [web-function.md](web-function.md), [run.md](run.md),
[sdk.md](sdk.md#embedding-a-function-page), [api-docs.md](api-docs.md).
