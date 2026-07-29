# Security

FuncToWeb publishes functions; the boundary with the host application is
explicit.

## What FuncToWeb does guarantee

* **Input is validated before the function is called**, recursively and against
  the declared contract. See [types.md](types.md).
* **File references never escape their directory**: `/upload`, `/returns/{ref}`
  and the pre-execution resolution all require a bare file name, with no
  separators, no `.` or `..` and no absolute path. Both `/returns/{ref}` and the
  pre-execution resolution also require the final path to have its root
  directory as its immediate parent and to be an existing file. A `..`, a
  symbolic link pointing outside, a subdirectory or an absolute path from
  anywhere else are all rejected. See [files.md](files.md) and
  [outputs.md](outputs.md).
* **A local path never leaves the server**: a file travels as its reference in
  both directions. Whatever the client sends is a reference, and whatever a
  page publishes for a file —a prefill, an [`OpenForm`](open-form.md) opening,
  a default written in the signature— is a reference too. A file that storage
  does not own has no reference, so the page is not built: a prefill answers
  `400`, an `OpenForm` answers `500`, and a signature default makes the
  `WebFunction` impossible to build. A rejection names the file and not where
  it is kept: the storage directory is cut out of the message before it is
  emitted, so a `422` or a `400` from `IsPathFile` reads
  `not an accepted file type: 'notas.bin'`. See [files.md](files.md).
* **A published reference is immutable**: `/upload` responds `409` to any
  attempt to write it again —whether the file was already used or not— so
  knowing another user's reference does not let you replace their file. Once
  it has been used, the file is also permanent: the expiry of unused uploads
  never reaches it. See [files.md](files.md).
* **`/static/{path}` serves nothing outside its two directories**, although it
  does serve their subdirectories, and it responds `404` without distinguishing
  between "it is not there" and "you are not allowed to have it". See
  [static-assets.md](static-assets.md).
* **The interface writes all output as text, never as HTML.**

All three containments, uploads, returns and static assets, rest on the same
two checks: a filter on the name before anything touches the disk, and a
resolution that has to land under the root directory. The names the filter
refuses are in [files.md](files.md#reusable-references), and what `/static`
resolves against is in
[static-assets.md](static-assets.md#a-tree-not-a-list).

## What belongs to the host application

* **Authentication and authorization.** FuncToWeb provides none: what you mount
  is an `APIRouter`, and it inherits whatever the host application applies.
  `run()` protects nothing.
* **Per-file permissions** and the life cycle of what is uploaded and returned.
* **Execution limits**: FuncToWeb imposes no maximum time, no memory limit and
  no per-client concurrency limit.
* **Exposure of error messages**: the message of an exception travels to the
  client as is, so a function that writes internal data into that message
  publishes it.

## `hidden` hides, it does not protect

The `hidden` query parameter of a form opening takes a parameter out of view.
That is all it does: the value still travels in the body of the execution, and
anyone can call `/invoke` with a different one. A prefill does not lock a value
either. See [prefill.md](prefill.md).

## The prefill travels in the URL

It stays in the browser history, in the `Referer` header and in the server
access log. No channel available today avoids this, so data that must not be
logged must not travel as a prefill.

Related: [limitations.md](limitations.md), [files.md](files.md),
[http.md](http.md), [sdk.md](sdk.md#embedding-a-function-page).
