# Examples

The [documentation](../README.md#documentation) is the technical reference;
[`examples/`](../examples/) is the hands-on part, and it holds two kinds of file.

**Examples** teach **a single capability** and nothing else: 81 of them, in the
11 folders of the table below. **Mini-apps** live in [`project/`](../examples/project/) and
do the opposite — each one combines several capabilities into a small complete
application, to show how the pieces sit together once there is more than one.

Both kinds are runnable programs: a file with an `if __name__ == "__main__":`
guard, which is what the count in the main README means. That is every `.py`
file here, nothing in the collection is a module that only exists to be
imported.

## Running

```bash
python examples/basic/hello.py
python examples/project/todo.py
```

Examples and mini-apps alike serve at <http://127.0.0.1:8000> and block until
`Ctrl+C`. The clients in `examples/http/` exit on their own.

## Example folders

| Folder | What it teaches | Documentation |
| --- | --- | --- |
| [`basic/`](../examples/basic/) | `run()`, parameters, `WebFunction`, `WebFunctions`, space title, `page_of()` | [getting-started](getting-started.md), [web-function](web-function.md) |
| [`types/`](../examples/types/) | scalars, `date`, `time`, enums, optionals, lists, unions, dataclasses | [types](types.md) |
| [`validation/`](../examples/validation/) | `Min`, `Max`, `MultipleOf`, `Choices`, `Pattern`, `Slider`, `Rows`, `IsPassword`, `Color`, `Email`… | [types](types.md) |
| [`forms/`](../examples/forms/) | `OpenForm`, hidden fields and prefill via the URL | [prefill](prefill.md), [open-form](open-form.md) |
| [`files/`](../examples/files/) | `FileHint`, extensions, sizes, lists, references, storage on arrival, `max_upload_bytes`, expiry, storage location | [files](files.md) |
| [`outputs/`](../examples/outputs/) | text, multiple outputs, errors and `Download` | [outputs](outputs.md) |
| [`outputs_optional/`](../examples/outputs_optional/) | images and tables with optional dependencies | [outputs](outputs.md) |
| [`streaming/`](../examples/streaming/) | live `print()`, progress and `capture_prints` | [streaming](streaming.md) |
| [`fastapi/`](../examples/fastapi/) | `app_of()`, prefixes, your own routes, iframes, `sdk.js` and modals that run themselves | [application](router.md), [sdk](sdk.md) |
| [`themes/`](../examples/themes/) | `system`, `light` and `dark` in `run()` and `app_of()` | [static-assets](static-assets.md) |
| [`http/`](../examples/http/) | `/invoke`, `/invoke-stream`, `/upload` and `/doc` from a client | [http](http.md), [api-docs](api-docs.md) |

## Mini-apps

| Mini-app | What it combines | Documentation |
| --- | --- | --- |
| [`project/todo.py`](../examples/project/todo.py) | one dataclass model reused by three functions, `app_of()` under a prefix, a hand-written route of your own | [types](types.md), [application](router.md) |
| [`project/todo_stored.py`](../examples/project/todo_stored.py) | the same mini-app whose tasks survive the restart: the dict becomes a store and the model that draws the forms is what the JSON file holds | [types](types.md), [application](router.md) |

A mini-app is still short enough to read in one sitting, and it is still an
ordinary FastAPI application: the library contributes an application, never the
host.

## Dependencies

Everything works with `pip install func-to-web`, except
[`outputs_optional/`](#outputs-with-optional-dependencies), where each subfolder
declares its own (`pillow`, `matplotlib`, `pandas`, `polars`, `numpy`), and
[`project/todo_stored.py`](../examples/project/todo_stored.py), which needs
[`pytypehintstore`](https://github.com/offerrall/pytypehintstore). None of them
is required by the library.

The examples use fictional data, never access the Internet and write only to
the system temporary directories, with two deliberate exceptions:
[`files/storage_dir.py`](../examples/files/storage_dir.py) points `uploads_dir` at a
`storage/` folder beside itself, because where the files land is its lesson,
and [`project/todo_stored.py`](../examples/project/todo_stored.py) keeps its store in a
`data/` folder beside itself, for the same reason — the file it writes is what
it is teaching.

## Direct HTTP

How to call a function served by FuncToWeb without a browser. Everything runs on
the standard library (`urllib.request`): these examples need no `httpx`, no
`requests` and no other extra dependency.

### Files

* `server.py` — the space the other examples call: `greet` (success), `book`
  (rejects out-of-range values), `divide` (raises `ZeroDivisionError`),
  `countdown` (prints as it runs) and `measure` (receives a file).
  `app_with_prefix()` mounts the same space under a prefix, because every route
  is relative.
* `invoke_client.py` — reads `/doc` and calls `/invoke` four times: success, an
  out-of-range argument, an exception inside the function and an extra
  argument.
* `stream_client.py` — consumes the SSE events from `/invoke-stream`.
* `upload_client.py` — uploads a temporary file to `/upload` and reuses the
  reference in two invocations, plus one with a reference that does not exist.

### Running

Terminal 1:

```bash
python examples/http/server.py
```

Terminal 2:

```bash
python examples/http/invoke_client.py
python examples/http/stream_client.py
python examples/http/upload_client.py
```

If the server is not running, each client ends with a single
`no server at http://127.0.0.1:8000: ...` line and nothing else.

Nothing here is specific to Python: the raw byte channel is what the SDKs wrap,
and from a shell `curl --data-binary` with the two headers does the same.

Status codes: `200` means the function finished, `422` that the body breaks the
input contract, and `500` that the function raised an exception.
`/invoke-stream` always answers `200`, and the error is delivered inside the
`result` event.

### Under a prefix

Mounted with `app.mount("/tools", app_of(...))`, the routes
become `/tools/greet/invoke`, `/tools/upload` and `/tools/doc`. The clients only
need to change their `PREFIX` constant to `"/tools"`; `upload_client.py` takes
that constant from `invoke_client.py`, together with `invoke()`.

## Outputs with optional dependencies

Images and tables. FuncToWeb does not depend on any of these libraries or
import them: it checks whether the module is already loaded, so each
dependency is imported only inside its own example.

| Folder | Dependency | Installation | Output |
| --- | --- | --- | --- |
| `pillow/` | Pillow | `pip install pillow` | `image` |
| `matplotlib/` | matplotlib | `pip install matplotlib` | `image` |
| `pandas/` | pandas | `pip install pandas` | `table` |
| `polars/` | polars | `pip install polars` | `table` |
| `numpy/` | numpy | `pip install numpy` | `table` |

Each one is described below. None of these
libraries is a dependency of FuncToWeb, and none of them appears in
`pyproject.toml`: install only the one for the example you want to run.

The reference for the outputs contract is in [Outputs](outputs.md).

### Image with Pillow

Optional dependency: **Pillow**.

```bash
pip install pillow
```

`image.py` draws a square gradient with a frame and a label, and returns
the `PIL.Image.Image` object unchanged: FuncToWeb recognizes it as an image,
encodes it as a PNG, and sends it as a data URI inside an `image` output.

What it demonstrates:

* returning a Pillow image produces an `image` output, not the object's `str()`;
* FuncToWeb does not import Pillow: it detects Pillow because the example has
  already imported it, so the dependency lives only in this file;
* the color input uses the `Color` type.

Run it from the repository root:

```bash
python examples/outputs_optional/pillow/image.py
```

### Chart with matplotlib

Optional dependency: **matplotlib**.

```bash
pip install matplotlib
```

`figure.py` plots a sine wave and returns the `matplotlib.figure.Figure`, which
FuncToWeb saves as a PNG with `bbox_inches="tight"` and delivers as an `image`
output.

What it demonstrates:

* the **figure** is recognized, not the `Axes`: returning `axes` would produce
  its `str()` as text;
* the figure is built with `Figure(...)`, without `pyplot`: there is no backend
  to choose, no window opens, and the figure never enters the global `pyplot`
  registry;
* if you use `pyplot`, set a non-interactive backend first with
  `matplotlib.use("Agg")`; FuncToWeb closes the figure with `pyplot.close()`.

Run it from the repository root:

```bash
python examples/outputs_optional/matplotlib/figure.py
```

### Table with pandas

Optional dependency: **pandas**.

```bash
pip install pandas
```

`dataframe.py` builds a sales report in memory and returns the
`pandas.DataFrame`, which is converted into a `table` output with the column
names as headers.

What it demonstrates:

* a `DataFrame` is a table; a plain `list` or `dict` is not, and would be
  displayed with `str()`;
* the headers are the column names, and every cell goes through `str()`;
* the rows are read with `itertuples()`, which preserves the type of each
  column: an `int64` next to a `float64` is not promoted, and `86` does not
  come out as `86.0`.

Run it from the repository root:

```bash
python examples/outputs_optional/pandas/dataframe.py
```

### Table with polars

Optional dependency: **polars**.

```bash
pip install polars
```

`dataframe.py` builds an inventory report in memory, adds a computed column,
and returns the `polars.DataFrame`, which is converted into a `table` output.

What it demonstrates:

* polars works just like pandas: FuncToWeb recognizes both without depending on
  or importing either;
* the headers are the column names, and the rows come from `rows()`;
* the optional filter can leave the table empty, and that is still a `table`
  output, just without rows.

Run it from the repository root:

```bash
python examples/outputs_optional/polars/dataframe.py
```

### Table with numpy

Optional dependency: **numpy**.

```bash
pip install numpy
```

`matrix.py` builds an operation table using broadcasting and returns the
two-dimensional `numpy.ndarray`, which is converted into a `table` output.

What it demonstrates:

* a numpy array becomes a table only if it has exactly two dimensions: a 1D or
  a 3D array does not, and would end up as text;
* since there are no column names, the headers are generated: `Column 1`,
  `Column 2`, …;
* every cell is converted with `str()`, so a `numpy.int64` is serialized like
  any other value, regardless of its type.

Run it from the repository root:

```bash
python examples/outputs_optional/numpy/matrix.py
```
