# Getting started

```bash
pip install func-to-web
```

## A function and its web page

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

`run()` starts the application at `http://127.0.0.1:8000` and blocks until it
stops. These four routes are the ones you use directly:

```text
/                  the index, with one entry per function
/volume/           the form
/volume/invoke     the execution
/doc               the space contract, in plain text
```

They are not the only ones: the application also serves `/volume/invoke-stream`,
the same execution streamed over SSE, and `/static/{path}`, the assets shared by
the pages. The complete list is in [run.md](run.md).

The form already knows that `width` and `height` range from 1 to 100, and that
`depth` is 10 if you leave it alone: the limits come from the signature, and
the docstring becomes the description shown on the page and in `/doc`.

The same call works from any client:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"width": 3, "height": 4}' \
  http://127.0.0.1:8000/volume/invoke
```

```json
{"result": {"type": "text", "value": "120"}}
```

The `-> float` describes the signature; it does not coerce the return value:
`3 * 4 * 10` with integers returns an `int`, and FuncToWeb writes the output
with `str()`.

## Several functions and metadata

`run()` accepts a list, and [`WebFunction`](web-function.md) gives a name,
description or slug of its own to any function that needs one:

```python
from func_to_web import WebFunction, run


def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    return a / b


run(
    [volume, WebFunction(divide, name="Divide numbers", slug="division")],
    title="Internal tools",
)
```

## Inside an existing application

When you already have a FastAPI application, mount the FuncToWeb ASGI app:

```python
from fastapi import FastAPI

from func_to_web import app_of


app = FastAPI()
app.mount("/tools", app_of([volume, divide]))
```

`run()` is for when the tool is all there is; `app_of()` is for everything
else. The contract for each is in [run.md](run.md) and
[router.md](router.md).

## What to read next

* Which types and constraints a parameter accepts: [types.md](types.md).
* How to open a form with values already set: [prefill.md](prefill.md).
* What a function can return: [outputs.md](outputs.md).
* How to call a function from a script: [http.md](http.md).
