# Files

A `str` annotated with `FileHint(...)` declares a file reference: which
extensions it accepts and, optionally, how large it may be. The core reads the
extension and builds the argument, `pytypehintweb` generates the widget and the
transport and applies the size bounds to the file the user picks, and FuncToWeb
provides the upload channel, the storage and the resolution from reference to
local path.

```python
from typing import Annotated

from PIL import Image

from func_to_web import FileHint, Max, Min


ImagePath = Annotated[str, FileHint(extensions=(".png", ".jpg", ".jpeg"))]


def blur(image: ImagePath, radius: int = 8) -> str:
    with Image.open(image) as picture:
        ...
```

Pillow is not a FuncToWeb dependency: here it only opens the image, as any other
library would.

The function receives a `str` with the local path of the already stored file
(not bytes, not an `UploadFile`) and opens it directly. The function knows
nothing about HTTP, nothing about the upload cycle, nothing about where
FuncToWeb stores it.

```text
in transport      → unique reference (a str)
in the function   → str with the full local path
```

## What `FileHint` checks, and where

The annotation describes more than the widget, but no single layer applies all
of it. Each half is enforced where the information it needs actually lives:

```text
extension    pytypehint, on the text of the value, compared in lowercase
             — both for a path written in the signature and for whatever
               the resolver returned
min_size     the browser, on the local File it has just been handed
max_size     the browser, on that same File
```

`Signature.build()` reads the value as a string. It does not open the file, it
does not stat it and it does not ask whether it is there: existence and
confinement to the storage directory are FuncToWeb's rules, applied by the
resolver before the core ever sees the value →
[From reference to path](#from-reference-to-path).

```python
MEGABYTE = 1024 * 1024

DataFile = Annotated[
    str,
    FileHint(extensions=(".csv",), min_size=100, max_size=2 * MEGABYTE),
]


def preview(table: DataFile) -> str:
    ...
```

Both limits are in bytes and apply **per file**, never as a total: three 4 MB
files under a `max_size` of 5 MB are three valid files, and counting them is
still the job of the list's `Min`/`Max`. A file exactly at the limit is inside;
one byte more is outside. They travel in the plan as `minSize` and `maxSize`,
which is how the browser comes to know them, and the declaration itself is
checked when the atom is built:

| Declaration | Error |
| --- | --- |
| a limit that is neither `int` nor `None` | `TypeError` |
| a negative limit | `ValueError` |
| a `min_size` greater than `max_size` | `ValueError` |

The extension check happens before the function is called, so over HTTP it is a
`422` with the core's message:

```text
{"error": "SchemaValueError: table: not an accepted file type: 'notas.txt', expected one of ('.csv',)"}
```

There is no equivalent `422` for the byte bounds, and there is no server-side
check behind the browser's. A reference the browser never weighed —one typed by
hand, one restored with [`setValue()`](#putting-a-reference-back-setvalue), one
sent by a script— reaches the function whatever its size, and a file whose
bytes change on disk after it was uploaded is never measured again. What a size
bound buys is a form that refuses to upload; a guarantee that has to hold
against any client belongs to the function itself, or to the host application.
Why the split falls there →
[design/files.md](design/files.md#why-upload-does-not-apply-filehintmax_size).

### Declaring a file default

A default written in the signature is read at compile time, when there is still
no resolver to convert anything, so it is written as a real path on the server
—and that path has to name a file sitting directly in `UPLOADS_DIR`, the
storage directory `run()` announces at startup:

```python
DataFile = Annotated[str, FileHint(extensions=(".csv",))]

STORED = "/home/ana/.local/share/FuncToWeb/uploads/baseline-1234.csv"


def preview(table: DataFile = STORED) -> str:
    ...
```

Two things break the build, before any page exists:

```text
SchemaValueError: table: default: not an accepted file type: '/home/ana/.local/share/FuncToWeb/uploads/notas.txt', expected one of ('.csv',)
SchemaValueError: table: default: file is not in the storage directory: 'baseline.csv'
```

Neither of them opens the file. A default naming a `.csv` that is not on disk
compiles, the page offers it as the current file, and the failure arrives on
the first execution as the resolver's `File not found`. Why the two quote
different things is a matter of who speaks →
[design/files.md](design/files.md#the-two-messages-of-a-file-default).

Putting the file there is the author's step: copy it into `UPLOADS_DIR` by
hand, or upload it through `/upload` and use it once, because an upload waits
[pending](#pending-and-promoted-files) under a name of its own and is not yet
sitting there under the bare name the default has to write. Either way the
name it ends up under is its reference, and that reference is the only thing
the plan publishes: the path stays on the server.

## Two endpoints, two jobs

```text
POST {prefix}/upload          bytes  → stored file
POST {prefix}/{slug}/invoke   JSON   → execution
```

`/upload` moves bytes; `/invoke` carries a JSON object in which a file is an
ordinary string. `/upload` is registered once per application, and only if at least
one of its functions has a file field.

## Maximum size per file

`max_upload_bytes` sets the maximum size of each file received by `/upload`, for
the whole space:

```python
app_of(functions, max_upload_bytes=50 * 1024 * 1024)
```

```text
None            no limit imposed by FuncToWeb
an int > 0      maximum per file, in bytes
```

It applies **per request**, so a form with several files checks each one
separately: two 40 MB files pass under a 50 MB limit even though together they
add up to 80. A file exactly the size of the limit is accepted.

The size is counted as the chunks arrive: as soon as it is exceeded, writing
stops, the partial file is deleted, and the response is

```text
413 {"detail": "uploaded file exceeds the maximum size of 52428800 bytes"}
```

A `Content-Length` that already declares more than the limit is rejected before
any writing starts, but it is not trusted: it can be missing or wrong, and the
real check is the one made chunk by chunk. A `max_upload_bytes` that is neither
`int` nor `None` is a `TypeError` when the application is built, and `0` or a
negative one a `ValueError`.

In the interface, the upload modal shows the server message next to the file
that failed, and anything still pending is retried with Submit.

The `FileHint` limits belong to the parameter, and `/upload` does **not** apply
them:

```text
max_upload_bytes         operational ceiling of the endpoint, counts the real
                         bytes as they arrive, cuts early
FileHint.min/max_size    parameter constraint, applied by the browser to the
                         File it is holding, and by nobody once that file has
                         become a reference
```

Which of the two rejects a file decides the answer you get:

| Situation | Answer |
| --- | --- |
| Upload too large for the server | `/upload` responds `413` |
| A local `File` that breaks the field's bound | the form neither uploads nor sends it |
| A reference from outside that breaks the bound | `/upload` accepts it and `/invoke` runs the function |
| A reference that names nothing in storage | `/invoke` responds `422` |

`max_upload_bytes` is the only byte ceiling no client can skip, and that is
deliberate rather than an omission: why the endpoint does not apply the field
limit, and why nothing behind it does either →
[design/files.md](design/files.md#why-upload-does-not-apply-filehintmax_size).

## Reusable references

The browser mints the reference when the user chooses a file:

```text
annual-report-<uuid>.pdf
└─────┬─────┘ └──┬─┘ └┬┘
  ASCII slug     │    lowercase extension
  of the name    │
  (≤15 chars)    new UUID
```

In the form's own flow it is the only source of *new* references: the interface
never manufactures a choice that the user did not make. The UUID makes sure that
two users uploading their own `report.pdf` do not share a destination.

A reference is a file name and nothing more — and one that all three platforms
can store. `/upload` checks this **before touching the disk**, and any breach
gets a `400`:

```text
X-File-Reference: ../evil.pdf   → 400 cannot contain separators
X-File-Reference: ..            → 400 must be a file name
X-File-Reference: a<b.pdf       → 400 cannot contain any of <>:"|?*
X-File-Reference: report.       → 400 cannot end with a dot or a space
X-File-Reference: NUL           → 400 is a reserved device name
X-File-Reference: ~pa.pdf       → 400 cannot start with the reserved prefix '~p'
X-File-Reference: ~ra.pdf       → 400 cannot start with the reserved prefix '~r'
X-File-Reference: <205+ bytes>  → 400 is longer than 204 bytes
```

The rules are the same on Linux, macOS and Windows even though only one of the
three demands some of them. `~p` and `~r` are refused because storage uses them,
and only them, to mark a date it wrote itself: `~p` for a file that is still
[pending](#pending-and-promoted-files), `~r` for a
[returned file](outputs.md#where-the-files-live) waiting to be fetched. The same
check applies to a reference arriving at an execution or a prefill, and to the
name a `Download` declares, so neither prefix can ever be named from outside.
The price is the same one in both cases: a file name of your own that begins
with those two characters —a plain `~` does not count— is not accepted.

Why one portable behavior, and why the two markers are refused at the door →
[design/files.md](design/files.md#why-the-name-rules-are-portable).

The length limit is 204 bytes, derived from the 255 of `NAME_MAX`
([design/files.md](design/files.md#where-the-204-bytes-come-from)). It is a
**writing** rule only: the resolver does not measure names, so a longer name
that is already sitting in the storage directory keeps resolving from disk.
What it cannot do is be uploaded, which for a stored reference is a `409`
anyway.

That limit protects the length of the file **name**. The length of the **full
path** also depends on where `UPLOADS_DIR` is and on the environment: on Windows
without long path support, a very deep data location can push the full path past
the system limit. If that happens, the fix is to point `uploads_dir` at a
shorter location or to enable long path support.

Validating the shape before writing is what keeps the division of blame honest:
an impossible name is the client's business and is rejected with a `400`, and
whatever fails afterwards (a full disk, permissions, a file system lock) is the
server's business and gets a `500`.

The shape is not the only thing checked. A reference whose file is already
stored is not uploaded twice: `/upload` responds
`409 {"detail": "a file with this reference already exists"}` before reading the
body, and the bytes on disk are left untouched. Already stored means either of
its two forms, promoted or still [pending](#pending-and-promoted-files), with
any date: what identifies a file is its bare reference and nothing else.

Why a second POST to the same reference is not a legitimate flow is the
reasoning behind that `409` →
[design/files.md](design/files.md#why-a-second-upload-of-the-same-reference-is-a-409).

The consequence is the part that matters: **a published reference is
[immutable](#what-the-guarantee-means)**. What fails *before* publishing does
not reserve the name: a `413`, a dropped connection or a failed publish leave
nothing behind, and that same reference can be retried.

### When bytes are uploaded

```text
reference with a local File      → newly chosen file  → uploaded before invoke
reference without a local File   → file already there → not uploaded
```

When you press Submit, the form collects what is still pending. Only those files
travel, one by one, with progress measured in bytes, behind a modal. When an
upload is confirmed, that reference never becomes pending again. If one fails,
the rest stay pending and pressing Submit again retries from there, without
repeating what was already confirmed.

Why that progress decides the transport the browser uses, and why the body is
the raw `File`, is the client side of the upload →
[design/files.md](design/files.md#the-client-side-of-the-upload).

The server streams the write to a temporary file and publishes it with an
atomic `os.replace`, under `UPLOADS_DIR`:

```text
UPLOADS_DIR/<reference>.<uuid>.part    ← written here
UPLOADS_DIR/~p<date>~<reference>       ← appears whole or does not appear
```

`UPLOADS_DIR` is the storage directory of the process: the user's data
directory unless the `uploads_dir` argument of
[`app_of()`](router.md#the-arguments) or the `FUNCTOWEB_UPLOADS_DIR`
variable names another one, and it is settled
[once per process](router.md#one-process-one-policy), not once per application.

The name it appears under carries the moment it landed, because an upload that
no execution ever uses expires; the [next section](#pending-and-promoted-files)
covers that cycle. The client never sees that name.

The `uuid` of the partial file covers the only window the `409` does not reach:
two simultaneous first uploads of the same reference. Each writes its own
partial file, so the file that remains is one of the two payloads intact, never
a mix, and a publish that keeps failing where the race does not explain it
surfaces as a `500`.

What two simultaneous uploads do to each other, and why `os.replace()` is
retried on Windows, is that race written out →
[design/files.md](design/files.md#two-simultaneous-uploads).

### One transfer, many executions

```python
PdfPath = Annotated[str, FileHint(extensions=(".pdf",))]


def analyse(document: PdfPath, threshold: float) -> str:
    ...
```

```text
threshold = 0.2   → POST /upload (the bytes) + POST /invoke
threshold = 0.5   → POST /invoke: same reference, only the JSON form
threshold = 0.8   → POST /invoke
```

The large file travels once; changing any other parameter does not move it
again. That is what makes it comfortable to try out configurations on a large
file, especially on a local network, where the transfer is the slow part.

An HTTP client that already knows a reference does not need `/upload` at all:

```text
POST /tools/analyse/invoke
{"document": "annual-report-<uuid>.pdf", "threshold": 0.5}
```

### Putting a reference back: `setValue()`

A reference is a `str`: it can be stored in a database, returned by a query and
put back into a form.

```javascript
widget.setValue("annual-report-<uuid>.pdf")
```

A value set this way counts as an **existing** file, not as a choice: the widget
labels it as such ("Current file: …"), `value()` and `read()` carry it
literally, it is never pending, it must pass the same extension filter, and
`setValue(null)` clears it. Choosing a file replaces it with a new reference,
and a ↺ button undoes that.

The label is shortened: it shows the file name, or the last 32 characters behind
a `…` when the reference has no file name to cut at. That is presentation only,
and it belongs to the widget, not to this layer. The full value is what `read()`
returns and what travels to `/invoke`.

That same mechanism is what lets a [prefill](prefill.md) supply a file: the
value travels as a reference, it is resolved and its extension checked before
the page is served, and it reaches the widget as the current file.

```text
GET /describe/?prefill={"document": "annual-report-<uuid>.pdf"}
→ 200, with the file already in place and no pending upload
```

## Pending and promoted files

An uploaded file has two states, and only the first one expires:

```text
pending     just uploaded, nobody has used it yet   → deleted after the TTL
promoted    some execution or prefill used it       → permanent, never touched
```

`/upload` publishes into the first state, under a name that carries the second
the bytes landed:

```text
~p1767225600~annual-report-<uuid>.pdf
└┬┘└────┬───┘└──────────┬────────────┘
 │      │               the reference, untouched
 │      Unix epoch in seconds, exactly ten digits
 the mark, closed with ~
```

The first successful resolution of that reference renames the file to the bare
name, and from then on nothing ever renames or deletes it again. **The client
never sees the prefix**: it uploads, invokes, prefills and receives the bare
reference everywhere, and the resolver only ever hands out the bare path. The
prefix is a fact about the disk, not about the protocol.

Do not confuse this *pending* with the form's: there, a file is pending while
it still has to be uploaded. Here, it is pending once it is already stored and
still waiting to be used.

### What counts as using it

Any successful resolution, no matter which endpoint asks for it:

```text
POST /{slug}/invoke          promotes
POST /{slug}/invoke-stream   promotes
GET  /{slug}/?prefill=…      promotes
```

They all go through the same resolver, so there is a single rule. An `/upload`
does not promote anything, and neither does an execution that fails afterwards:
what promotes is resolving the reference, before the function is even called.
Any expired file it walks past on the way is deleted there and then, instead of
being left for the sweep.

### Expiry

A pending file that is not used within `pending_ttl` (one hour by default;
[`app_of()`](router.md), [`run()`](run.md)) is deleted:

```text
resolving an expired reference   → deleted, and the answer is the usual
                                   "File not found: <reference>"
never resolved at all            → a background sweep deletes it
```

The sweep runs in one daemon thread per process, every 30 to 60 minutes,
drawn again each cycle so that workers started together drift apart instead of
sweeping in lockstep. It also runs once when the application is built, for
processes too short-lived for the thread to ever wake up. It deletes expired
pending files, anything carrying the mark that does not parse (the server
never writes such a name), and `.part` files older than the TTL, left behind by
interrupted uploads. It never touches a promoted file, a live pending one or a
fresh partial, and it never fails a request: an error on one entry is ignored
and retried on the next cycle.

That thread is one per process and not one per directory: the same cycle makes
a second pass over the returns directory, with its own TTL and its own rule.
See [outputs.md](outputs.md#where-the-files-live).

### What the guarantee means

```text
pending     effective staging: it exists, it is not yet permanent
promoted    immutable and permanent
```

**A published reference is immutable**, and promotion is where that starts to
hold: the bytes a promoted reference names are the ones it will always name,
and the file stays there. Storing the reference and reusing it is safe, with no
asterisk, from the first use onwards.

Promotion is the handover; the retention of used files is the host's →
[design/files.md](design/files.md#custody-after-promotion).

The other half of the contract: **a reference uploaded and never used
expires**. Uploading today and invoking tomorrow works only if the interval
fits inside the TTL:

```python
app_of(functions, pending_ttl=timedelta(days=7))   # a longer window
app_of(functions, pending_ttl=None)                # no expiry at all
```

With `pending_ttl=None` there is no thread, no sweep and no prefix: `/upload`
publishes the bare name directly. A file already sitting in `UPLOADS_DIR` under
a bare name is seen as promoted, whoever put it there: nothing is deleted
retroactively and the migration needs no step.

## From reference to path

The reference is transport; the function never sees it. The swap is done by
`decode()`, the same call that already prepares dates, floats and enums.
FuncToWeb hands it a `file_resolver`, and `decode()` calls it on every value
that belongs to a file field, at any depth: a plain field, a list element by
element, inside a dataclass, or in the active branch of a union. What decides
the call is the declared type, never the content: a `str` in another field that
happens to look like a reference is left alone.

The only thing FuncToWeb adds is the storage policy: the reference is resolved
under `UPLOADS_DIR`, it has to land directly inside it, and the file must exist
—as the bare name, or as a pending file it then
[promotes](#pending-and-promoted-files). Otherwise the function is not called:

```text
{"error": "FileNotFoundError: File not found: nope-0000.pdf"}
{"error": "ValueError: invalid file reference '../evil.pdf': is not a file of the storage directory"}
```

It is the same resolver in both execution endpoints and in the prefill, so the
storage rule is written only once — and it is the only place existence is
checked at all. What comes out of it is a local path that keeps the extension
of the reference, which is exactly what the core then reads; a value the
resolver refuses never reaches the core. Why nothing behind it checks the same
thing again →
[design/files.md](design/files.md#why-existence-belongs-to-the-resolver).

A reference is a bare file name, reading and writing alike: a path, absolute or
with separators, is not a reference and the resolver refuses it. What decides is
the resolution as well as the string —the final path must have `UPLOADS_DIR` as
its immediate parent— so `..`, a symbolic link pointing outside, or a
subdirectory are all rejected just the same.

The traffic in the other direction obeys the same rule: what a plan publishes
for a file, whether it comes from a prefill, from an [`OpenForm`](open-form.md)
or from a default in the signature, is the reference and never the path. See
[security.md](security.md).

That draws the border neatly. A path is written in exactly one place, the
signature, and it is the one place where the author is the one writing.
Everything on the client's side of the border —what arrives, what is published,
what a rejection says— is a reference. Why the signature default is the only
sentence spoken on the other side of that border →
[design/files.md](design/files.md#the-authorclient-border).

## Multiple files

`list[ImagePath]` is the multiple selection, and the list's bounds are bounds on
the number of files:

```python
def montage(
    images: Annotated[list[ImagePath], Min(1), Max(3)],
) -> Image.Image:
    ...
```

Each choice adds to the list, each file mints its own reference, each row has
its `×` and the `+` opens another picker. The transport is a list of strings and
recursive validation reaches every element:

```text
{"images": ["a.png", "b.png", "c.png", "d.png"]}
→ images: too many items: 4, maximum 3

{"images": ["notas.txt"]}
→ images: [0]: not an accepted file type: 'notas.txt', expected one of ('.png', '.jpg', '.jpeg')
```

Both messages assume references that are already stored: the core checks the
extension against the path the resolver returned, and the message names that
file by its reference, with the storage directory cut out before it is sent. If
the file is not stored, the error is a different one and arrives earlier:

```text
{"error": "FileNotFoundError: File not found: notas.txt"}
```

References in a list that have already been confirmed are not uploaded again
either.

## What it is and what it is not

This is **persistent reuse by reference**, not an HTTP cache: there is no
deduplication by content, no hashing, no invalidation and no synchronization
between servers. Once the reference of a promoted file is lost, the file is
still on disk but nobody knows how to name it. What remains the host
application's job:

* **storing the reference** if it wants to reuse it — the one from the form, not
  the path the function receives, which depends on where this server stores its
  files;
* **the life cycle** of promoted files: how long they are kept and when they
  are deleted;
* **authorization**: the endpoint inherits the host application's
  authentication, and FuncToWeb does not add per-file permissions. See
  [security.md](security.md).

*Output* files are a different matter: see [outputs.md](outputs.md).

Related: [types.md](types.md), [prefill.md](prefill.md), [http.md](http.md),
[limitations.md](limitations.md), [design/files.md](design/files.md).
