# Outputs

A successful execution produces one or more outputs, of five types: `text`,
`image`, `table`, `download` and `form`.

The first three are decided by the **return value**; for an ordinary output the
annotation plays no part, and `-> str`, `-> Any` or no annotation at all give the
same result. The other two are **declared** in the return annotation:
[`Download`](#downloads) and [`OpenForm`](open-form.md); without the marker they
do not exist.

Outputs do not depend on the endpoint: `/invoke` and
[`/invoke-stream`](streaming.md) produce exactly the same ones, in the same
order.

If the function returns a value that meets its contract, there are outputs; if it
raises, there is an error. Returning is not enough on its own, though: a return
value that breaks what was declared is also an error, even when the function
raised nothing (see [a broken contract](#a-broken-contract)). Errors travel in
`error`, never alongside `result`. A return value that cannot be represented
does not become an error: the call finished well, and that is what is reported.

## The traversal

There is only one traversal; it is recursive, and it tries the following in
order:

```text
1. a DataFrame or a 2D array  → a single table output
2. an empty list or tuple     → a text output with "Done"
3. a list or tuple with items → walked and flattened, in order
4. None                       → a text output with "Done"
5. a download (Download)      → a download output
6. a Pillow image             → an image output
7. a matplotlib figure        → an image output
8. anything else              → a text output with str(value)
```

An outer `list` or `tuple` means "several outputs", and it is flattened to any
depth. The table check is repeated on every element, so a table can appear inside
a collection.

```text
[1, 2, 3]                    → three texts
["Finished", [1, 2, 3]]      → four texts
["Finished", frame, image]   → text, table, image
[{"name": "Ana"}, {…}]       → two texts, one per dict
```

Only `None` and empty collections give `"Done"`. Any other value that is not
recognized is shown with `str(value)`, so a `bool` gives `"True"` and a bare
`dict` gives its repr.

A collection that contains itself is not walked forever: it is detected by
identity against the active stack and fails with
`ReturnContractError: recursive output collection`. Repeating the same object in
two positions is not a cycle.

## Images

FuncToWeb does not depend on Pillow or on matplotlib, and imports neither: it
looks the module up among those already imported, so a function that returns an
image must have imported it first.

The image is encoded as PNG and sent in full as a data URI, with no separate
storage and no separate URL:

```json
{"type": "image", "value": "data:image/png;base64,iVBORw0KGgo…"}
```

Modes that PNG cannot store, `CMYK` for example, are converted to `RGB` before
encoding.

A `matplotlib.figure.Figure` produces the same output: it is saved with
`bbox_inches="tight"`, so the bounding box fits the content, and it is then
closed with `pyplot.close()` if `pyplot` is loaded
([design/outputs.md](design/outputs.md)).

What is recognized is the figure, not an `Axes`: returning `ax` instead of `fig`
gives the text of its `str()`, which is the sign that the `fig` is missing.

## Tables

Only three values produce a `table` output, and all three **say** they are a
table:

| Return value | Headers |
| --- | --- |
| pandas `DataFrame` | its column names |
| polars `DataFrame` | its column names |
| 2D numpy array | generated: `Column 1`, `Column 2`, … |

```json
{"result": {"type": "table",
            "headers": ["name", "age"],
            "rows": [["Alice", "25"], ["Bob", "30"]]}}
```

An ordinary `list`, `tuple` or `dict` is **not** a table: neither the shape nor
the headers are guessed. A list of dicts is a collection of outputs, and each
dict is shown with `str()`; if what you want is a table, `pd.DataFrame(rows)`
is one line. A numpy array that does not have exactly two dimensions is not a
table either.

A `table` output carries no `value`: it carries `headers` and `rows`, and **every
cell is converted with `str()`**, so serialization does not depend on the type:
a `Decimal`, a date and a `numpy.int64` all arrive as text. With pandas the rows
are read with `itertuples()`, which preserves the type of each column
([design/outputs.md](design/outputs.md)).

The check runs **before** a collection is broken apart, so a `DataFrame` inside a
list is still a table among the other outputs.

## Downloads

A downloadable file is marked in the return annotation with `Download`, applied
to a `Path`, a `str` holding a path, `bytes`, or lists and tuples of those. The
marker does not change the signature: the function still returns exactly what it
declared.

```python
from pathlib import Path
from typing import Annotated

from func_to_web import Download


def report() -> Annotated[Path, Download()]:
    return Path("/tmp/report.pdf")
```

`Download` is transport metadata: it does not wrap the value and it does not
change the signature. Without the marker, a returned `Path` is the text of its
path; with it, a `.png` is a download and not an image. Inside a `Download` a
`str` is read as a **path**, not as text, and a file can be generated entirely in
memory:

```python
def report() -> Annotated[bytes, Download(filename="report.pdf")]:
    return build_pdf_in_memory()
```

### The declared type is what you must return

Inside a `Download`, what you declare is not a hint: the return value is checked
against that type, and there is no courtesy conversion between them.

```text
Annotated[Path, Download()]        → a Path
Annotated[str, Download()]         → a str with the path to a file
Annotated[bytes, Download(...)]    → bytes
Annotated[Path | str, Download()]  → either of the two, never bytes
```

A `Path` where `str` was declared fails just like an `int`, even though they mean
the same thing to the file system. The message names both types:

```text
declared Path,       returned str    → expected Path for Download, got str
declared str,        returned Path   → expected str for Download, got Path
declared bytes,      returned str    → expected bytes for Download, got str
declared Path | str, returned bytes  → expected Path or str for Download, got bytes
```

The shape counts as much as the type: a declared list wants a list or a tuple,
and a single declared file does not accept a collection.

```text
declared list[Path], returned Path   → expected a list or tuple of files for Download, got Path
declared Path,       returned [p, p] → expected Path for Download, got list
```

Once that check passes there is one more, which is no longer about types: a
`Path` or a `str` is copied to the returns directory, so it has to name a file
that exists. A well-typed `str` that points at nothing, or at a folder, fails at
storage rather than as a contract breach:

```text
{"error": "FileNotFoundError: File not found: nope.pdf"}
{"error": "IsADirectoryError: Not a file: informes"}
```

`bytes` skips that, since it is written directly, but it needs `filename`,
because it carries no name of its own. All these failures, the type ones and the
disk ones, happen after the function has returned, so they are a `500` with the
message in `error` and no outputs.

### Several files and several outputs

A single `Download` can produce several files, and one return can combine
downloads with ordinary outputs while keeping the order:

```python
def process() -> tuple[
    str,
    Annotated[list[Path], Download()],
    Annotated[list[bytes], Download(
        filename=lambda _value, index: f"memory-{index + 1}.pdf"
    )],
]:
    return "Finished", disk_reports, memory_reports
```

That produces a `text` and then one `download` per file. A `Download` inside the
return does not turn the whole response into a download: the contract only
replaces the marked branches (the `Path` becomes the file that has already been
identified), and the same recursive traversal converts the rest.

### Names

| `filename` | File name |
| --- | --- |
| `None` | the basename, for `Path` and `str` |
| `None` with `bytes` | error: bytes have no name of their own |
| a `str` | that fixed name |
| a callable `(value, index) -> str` | whatever it returns, per file |

The callable receives the original value and its index within that `Download`;
the index starts at zero, respects the order and restarts for each independent
`Download`. A fixed name with more than one file is an error, because the names
would collide.

The final name must be a `str`, and it obeys **the same rules an upload
reference obeys**: the portable file name described in
[files.md](files.md#reusable-references), with the length measured against what
the returns directory adds instead of what the uploads one does. It is one rule,
not two, because the route that serves the file back applies exactly that rule
to the reference it receives.

The name is checked before anything is written, so a breach is a
`ReturnContractError` and no file is left behind:

```text
Download filename: cannot contain any of <>:"|?*, got 'a<b.txt'
Download filename: cannot end with a dot or a space, got 'report.txt '
```

### `None` and unions

A downloadable output can be declared optional, and then `None` means "no file".
The rule is precise: **`None` can replace a whole `Download` output, but it
cannot stand for one of its inner files.**

It matters a great deal whether the `Download` wraps the union or only one of its
branches:

```python
# allowed: the whole value is downloadable, whatever it is
Annotated[Path | str, Download()]

# allowed: optional download
Annotated[Path, Download()] | None

# not allowed: mixes a download with a normal output
Annotated[Path, Download()] | str
```

The last one is rejected when the `WebFunction` is built:

```text
ReturnContractError: a union cannot mix Download and ordinary return branches
```

For the same reason `Annotated[list[Path | None], Download()]` is rejected. To
return a text **or** a file, use different positions, not a union. Why the two
cannot be told apart is in [design/outputs.md](design/outputs.md).

### Where the files live

Each file is copied (or written, if it is `bytes`) to the returns directory,
under the operating system's temporary directory:

```text
<system temp>/FuncToWeb/returns/
```

* the original file is **never** moved and never deleted;
* the physical name carries a random identifier in front, so two returns with the
  same public name do not collide;
* writing goes through a `.part` and an `os.replace`, so a failure never leaves a
  half-written file;
* the physical name also carries the moment the file was stored: the file stays
  available for `returns_ttl` (one hour by default;
  [`router_of()`](router.md), [`run()`](run.md)) and is eligible for the sweep
  afterwards, so the TTL is a guaranteed minimum lifetime and not a maximum. A
  download link is for fetching, not for keeping: there is nothing to claim and
  nothing to promote, so fetching it changes nothing;
* the sweep that deletes it is the one the uploads directory already runs, in
  [its second pass](files.md#expiry), and it only removes what FuncToWeb wrote:
  this directory is shared with the operating system, and a name that does not
  parse —a stranger's file, or a return stored before the date existed— is left
  alone.

The browser only receives a reference, with no local path:

```json
{"type": "download", "value": "<reference>", "filename": "report.pdf"}
```

```text
GET {prefix}/returns/{reference}
```

The route validates the reference as a bare file name, requires the file to exist
inside the returns directory and answers `404` in any other case; the public name
travels in `Content-Disposition`. The route is only registered if some function
in the space declares a `Download`.

The reference is the physical name, `<identifier>.<date><public name>`, so the
name the user will see is carried inside it. That is what makes it possible to
serve `Content-Disposition` without keeping any state. What it does not carry
is any local path, and nothing outside the server reads its parts: for the
browser it is one opaque string, which is why its shape can change without the
contract changing.

### A broken contract

The return value is checked against the part of the contract that declares the
`Download`, and only against that. A breach is a `ReturnContractError` that
follows the normal error path, with no silent conversion and no fallback to
`"Done"`:

| Breach | Message |
| --- | --- |
| The value is not what the annotation declared | `expected bytes for Download, got Path` |
| The tuple has a different length | `expected 2 return elements, got 1` |
| A `None` where the return is not optional | `None is not allowed for this Download return` |
| `bytes` with no name to save them under | `bytes downloads require a filename` |
| A `filename` callable returning something else | `Download filename callable returned an invalid value: expected str, got int` |

The contract looks at the type and the shape, not at the disk: whether the path
exists is a matter for storage, and it surfaces later as `FileNotFoundError` or
`IsADirectoryError`. See [the declared type is what you must
return](#the-declared-type-is-what-you-must-return).

## Opening another form

The fifth output is declared by marking the whole return with `OpenForm`, and it
carries the URL that opens another function in the space:

```json
{"result": {"type": "form", "href": "../edit_product/?prefill=%7B…%7D&hidden=%5B…%5D"}}
```

It is the only output that appears on its own. The full contract is in
[open-form.md](open-form.md).

## The shape in the response

An output is an object with `type` and, except for `table` and `form`, `value`.
Several outputs are a list, in the order the function returned them:

```json
{"result": [{"type": "text", "value": "One"},
            {"type": "text", "value": "Two"}]}
```

## In the interface

Each output is drawn as a block inside the results container, which is emptied
before each execution:

| Output | How it is drawn |
| --- | --- |
| `text` | its text, written as text and never as HTML |
| `image` | an `<img>` with the data URI as `src` |
| `table` | a `<table>` with its headers and rows, also written as text |
| `download` | one `<a>` per file, with the visible name, and with no automatic download and no ZIP |

The table is shown exactly as it arrives, with no search box, no sorting and no
pagination; it can only scroll horizontally inside its block. The image is shown
with a limited height, but copy and download deliver the original.

Each block carries its actions on the right: copy for the text; copy and download
for the image and the table. The table is copied tab-separated, with the headers
first, so that it pastes into a spreadsheet. Downloading it generates a
`table.csv` in the browser, without asking the server for anything: commas,
`CRLF`, double quotes where they are needed and UTF-8 without BOM, ordinary CSV,
readable by `pandas.read_csv()` with no options.

The frontend checks the shape before drawing: an output with no known `type`, a
`value` that is not text, a table whose headers and rows are not lists of text,
or a download with no `filename` are shown as `Invalid server response` instead
of being rendered half-way.

Related: [http.md](http.md), [streaming.md](streaming.md),
[open-form.md](open-form.md), [limitations.md](limitations.md).
