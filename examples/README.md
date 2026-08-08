# FuncToWeb examples

[`docs/`](../docs/index.md) is the technical reference; this folder is the
hands-on part, and it holds two kinds of file.

**Examples** teach **a single capability** and nothing else: 81 of them, in the
11 folders of the table below. **Mini-apps** live in [`project/`](project/) and
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
| [`basic/`](basic/) | `run()`, parameters, `WebFunction`, `WebFunctions`, space title, `page_of()` | [getting-started](../docs/getting-started.md), [web-function](../docs/web-function.md) |
| [`types/`](types/) | scalars, `date`, `time`, enums, optionals, lists, unions, dataclasses | [types](../docs/types.md) |
| [`validation/`](validation/) | `Min`, `Max`, `MultipleOf`, `Choices`, `Pattern`, `Slider`, `Rows`, `IsPassword`, `Color`, `Email`… | [types](../docs/types.md) |
| [`forms/`](forms/) | `OpenForm`, hidden fields and prefill via the URL | [prefill](../docs/prefill.md), [open-form](../docs/open-form.md) |
| [`files/`](files/) | `IsPathFile`, extensions, sizes, lists, references, storage on arrival, `max_upload_bytes`, expiry, storage location | [files](../docs/files.md) |
| [`outputs/`](outputs/) | text, multiple outputs, errors and `Download` | [outputs](../docs/outputs.md) |
| [`outputs_optional/`](outputs_optional/) | images and tables with optional dependencies | [outputs](../docs/outputs.md) |
| [`streaming/`](streaming/) | live `print()`, progress and `capture_prints` | [streaming](../docs/streaming.md) |
| [`fastapi/`](fastapi/) | `router_of()`, prefixes, your own routes, iframes, `sdk.js` and modals that run themselves | [router](../docs/router.md), [sdk](../docs/sdk.md) |
| [`themes/`](themes/) | `system`, `light` and `dark` in `run()` and `router_of()` | [static-assets](../docs/static-assets.md) |
| [`http/`](http/) | `/invoke`, `/invoke-stream`, `/upload` and `/doc` from a client | [http](../docs/http.md), [api-docs](../docs/api-docs.md) |

## Mini-apps

| Mini-app | What it combines | Documentation |
| --- | --- | --- |
| [`project/todo.py`](project/todo.py) | one dataclass model reused by three functions, `router_of()` under a prefix, a hand-written route of your own | [types](../docs/types.md), [router](../docs/router.md) |
| [`project/todo_stored.py`](project/todo_stored.py) | the same mini-app whose tasks survive the restart: the dict becomes a store and the model that draws the forms is what the JSON file holds | [types](../docs/types.md), [router](../docs/router.md) |

A mini-app is still short enough to read in one sitting, and it is still an
ordinary FastAPI application: the library contributes a router, never the host.

## Dependencies

Everything works with `pip install func-to-web`, except
[`outputs_optional/`](outputs_optional/README.md), where each subfolder
declares its own (`pillow`, `matplotlib`, `pandas`, `polars`, `numpy`), and
[`project/todo_stored.py`](project/todo_stored.py), which needs
[`pytypehintstore`](https://github.com/offerrall/pytypehintstore). None of them
is required by the library.

The examples use fictional data, never access the Internet and write only to
the system temporary directories, with two deliberate exceptions:
[`files/storage_dir.py`](files/storage_dir.py) points `uploads_dir` at a
`storage/` folder beside itself, because where the files land is its lesson,
and [`project/todo_stored.py`](project/todo_stored.py) keeps its store in a
`data/` folder beside itself, for the same reason — the file it writes is what
it is teaching.
