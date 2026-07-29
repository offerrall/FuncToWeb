# FuncToWeb examples

[`docs/`](../docs/index.md) is the technical reference; this folder is the
hands-on part. Each file is a runnable program that teaches **a single
capability** and nothing else.

A **runnable program** is a file with an `if __name__ == "__main__":` guard,
and that is what the count in the main README means. There are 80 of them
across the 11 folders, which is every `.py` file here: nothing in the
collection is a module that only exists to be imported.

## Running

```bash
python examples/basic/hello.py
```

Each example serves at <http://127.0.0.1:8000> and blocks until `Ctrl+C`. The
clients in `examples/http/` exit on their own.

## Folders

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
| [`fastapi/`](fastapi/) | `router_of()`, prefixes, your own routes, iframes and `sdk.js` | [router](../docs/router.md), [sdk](../docs/sdk.md) |
| [`themes/`](themes/) | `system`, `light` and `dark` in `run()` and `router_of()` | [static-assets](../docs/static-assets.md) |
| [`http/`](http/) | `/invoke`, `/invoke-stream`, `/upload` and `/doc` from a client | [http](../docs/http.md), [api-docs](../docs/api-docs.md) |

## Dependencies

Everything works with `pip install func-to-web`, except
[`outputs_optional/`](outputs_optional/README.md), where each subfolder
declares its own (`pillow`, `matplotlib`, `pandas`, `polars`, `numpy`). None
of them is required by the library.

The examples use fictional data, never access the Internet and write only to
the system temporary directories, with one deliberate exception:
[`files/storage_dir.py`](files/storage_dir.py) points `uploads_dir` at a
`storage/` folder beside itself, because where the files land is its lesson.
