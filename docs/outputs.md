# Outputs

What the function returns decides what the page shows:

| Return value | Output |
| --- | --- |
| `None`, or an empty list | the text `Done` |
| a pandas or polars `DataFrame`, a 2D numpy array | a table |
| a Pillow image, a matplotlib figure | an image |
| a `list` or `tuple` | one output per item, in order |
| anything else | a text, with `str(value)` |

```python
def summary() -> tuple:
    return "Finished", frame, image   # a text, a table and an image
```

The annotation plays no part: `-> str`, `-> Any` or none give the same result.
Only two outputs are declared in it: a file to download and
[`OpenForm`](prefill.md#openform).

- **Tables** are only those three types; a list of dicts is several texts, and
  `pd.DataFrame(rows)` makes it a table. Every cell is sent as text.
- **Images** travel inside the response as a PNG. FuncToWeb never imports
  Pillow or matplotlib: a function that returns an image has imported them.
- On the page, each output has buttons to copy it, and images and tables to
  download them; a table downloads as CSV.

## Downloads

Mark the return with `Download` to offer a file instead of showing it:

```python
from pathlib import Path
from typing import Annotated

from func_to_web import Download


def report() -> Annotated[Path, Download()]:
    return Path("/tmp/report.pdf")


def invoice() -> Annotated[bytes, Download(filename="invoice.pdf")]:
    return b"%PDF-1.7 ..."
```

It accepts a `Path`, a `str` with a path, or `bytes` (with a `filename`), and
lists of them. The value must be the declared type: returning a `str` where
`Path` was declared is an error, not a conversion. `filename` can also be a
function `(value, index) -> str` that names each file of a list.

Downloads mix with other outputs, in order:

```python
def process() -> tuple[str, Annotated[list[Path], Download()]]:
    return "Finished", [Path("/tmp/a.pdf"), Path("/tmp/b.pdf")]
```

The file is copied to a returns directory (the original is never moved) and
served at `/returns/<reference>` for `returns_ttl`, one hour by default.
`Annotated[Path, Download()] | None` is an optional download; a union of a
download with a plain type is refused, because the value cannot say which
branch it came from.

## Errors

If the function raises, the page and the API show the error:
`{"error": "ZeroDivisionError: float division by zero"}`. A return that breaks
what was declared, such as a `Download` of the wrong type, is an error too:
`ReturnContractError: expected bytes for Download, got Path`.

<details>
<summary>How it works inside</summary>

**Rows are read with `itertuples()`**, not `values.tolist()`, which would turn
an `int64` column beside a `float64` one into floats (`1200` shown as
`1200.0`).

**A matplotlib figure is closed** with `pyplot.close()` after saving, when
`pyplot` is loaded; otherwise pyplot's global registry grows by one figure per
call.

**A collection that contains itself** is detected by identity and fails as
`ReturnContractError: recursive output collection`; the same object twice is
fine.

**The download reference** is the physical file name,
`<id>.<date><public name>`, so the route can send the public name in
`Content-Disposition` without keeping any state. The sweep that deletes expired
returns only removes names it can parse, because the returns directory lives in
the system's temporary directory beside other programs' files.

</details>
