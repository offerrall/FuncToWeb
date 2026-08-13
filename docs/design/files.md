# Files: the upload endpoint, the reference and custody

Why `/upload`, the reference and the pending cycle are built the way they are.
The contract — what `FileHint` checks and which layer checks it, the rejection
and limit tables, the pending/promoted cycle and the border between path and
reference — is in [files.md](../files.md).

## The two messages of a file default

The two [messages](../files.md#declaring-a-file-default) quote different things,
because two different layers say them. The first is the core reading the string
as the author typed it, before anything has looked at the disk, so it echoes
that string whole, directory included — the author is the one who wrote it, and
it never leaves the process. The second is FuncToWeb turning that path into the
reference it will publish, and by then the directory is the part that must not
travel, so only the name is left.

Neither of them touches the disk, and that is the honest shape of the check: the
core compares an extension, FuncToWeb asks whether the name round-trips inside
the storage directory. A default naming a file that is simply not there
satisfies both. It is not a gap the build could close cheaply either — the path
is read once, when the `WebFunction` is compiled, and a file that exists then
can be gone by the time the first request arrives, so the answer that matters is
the one the resolver gives on each execution.

## Why `/upload` does not apply `FileHint.max_size`

The `FileHint` limits belong to the parameter, and `/upload` does **not** apply
them. The reason is *not* that something behind it will: nothing on the server
weighs a stored file, so the endpoint is not standing aside for a verdict that
comes later — no verdict comes.

```text
max_upload_bytes         operational ceiling of the endpoint, counts the real
                         bytes as they arrive
FileHint.min/max_size    parameter constraint, applied by the browser to the
                         File it is holding
```

A request to `/upload` carries bytes and a reference, and nothing else. It does
not say which parameter that reference will end up in, and it cannot: the same
reference serves several executions, and it can feed two functions whose bounds
disagree. Inside a list, a union or a nested dataclass there is no node to point
at either. Applying the field limit there would mean walking the schema a second
time inside FuncToWeb — a second validator alongside pytypehint's, with its own
reading of the same atoms, drifting from it the first time the core changes.
That is the one thing this layer has undertaken not to build.

The two numbers are also different kinds of thing, and reading one as an
implementation of the other is what produces the wrong expectation.
`max_upload_bytes` is an operational policy of the endpoint: how much this
server is willing to receive and keep, whatever it later turns out to be for.
`FileHint.min_size`/`max_size` are part of the function's contract: what this
parameter is prepared to work with. One belongs to the deployment, the other to
the signature.

So each layer applies what it can genuinely know. The browser holds a real
`File` with a real `.size`, so it weighs it before anything is uploaded and, if
it is outside the bounds, no reference is minted and nothing stays pending (a
multiple selection with one bad file is rejected whole, not halfway). The
endpoint holds bytes on the wire, so it counts them, stops mid-write, deletes
the partial file and answers `413`. The core holds a string, so it reads its
extension. Nobody stats the stored file.

```text
upload too large for the server         → /upload responds 413
local File that breaks the bound        → the form neither uploads nor sends it
opaque reference that breaks the bound  → /upload accepts it, /invoke runs
reference that names nothing in storage → /invoke responds 422
```

A reference supplied from outside names a file the browser never saw: there is
no size to weigh, none is invented, and the server is not asked for one. A file
edited after it was uploaded is in the same position, and so is a hand-written
client. The size bound is simply not applied to any of them, and saying
otherwise would be selling a guarantee this layer does not hold.

That is a deliberate boundary, not an open hole. An application that needs an
authoritative rule about the size of stored content owns that rule: it can check
it inside the function, which is the one place that has both the path and the
contract in hand, or in whatever wraps the mount. FuncToWeb does not invent that
policy on its behalf, and the one ceiling it does own, `max_upload_bytes`, it
enforces on the bytes themselves, where no client can talk it out of the number.

## Why the name rules are portable

The browser mints the reference as `<slug>-<uuid>.<ext>`, so none of those names
can come from there, and a single portable behavior is worth more than accepting
a name on Linux that breaks on Windows.

It is one rule for the two directories, and refusing the two markers at the door
is what makes them trustworthy: if a name on disk carries one, the server wrote
it.

## Where the 204 bytes come from

The length limit is not a hand-written number: it is the 255 bytes of `NAME_MAX`
minus the two things publishing adds to a name, the `.<32 hex>.part` suffix of
the partial file and the fixed 13 bytes of the pending prefix.

## Why a second upload of the same reference is a 409

The form never produces that case, since a confirmed upload never becomes
pending again, so a second POST to the same reference is not a legitimate flow:
it would be a confused client, or someone who knows a reference that is not
theirs (references travel in the URL of a prefill and in the `href` of an
`OpenForm`) overwriting another person's file.

## The client side of the upload

That progress is the reason the upload uses `XMLHttpRequest` and not `fetch()`:
it is the only one that reports the bytes sent. The body is the raw `File`, not
wrapped in `FormData`, so the browser streams it instead of holding the whole
file in memory.

## Two simultaneous uploads

The `uuid` of the partial file covers the only window the `409` does not reach:
two simultaneous first uploads of the same reference, when neither has published
yet and both see the name free. Each writes its own partial file and publishes
at the end, so the file that remains is one of the two payloads intact, never a
mix; outside that race the second one never even gets to write. On Windows,
`os.replace()` can fail with `PermissionError` if
both publish at once; that window lasts microseconds, so it is retried a handful
of times with a short pause. If the error persists after the retries
(permissions, antivirus, disk, a lock that will not go away), it is no longer
the race and it is not the client's fault either: the exception surfaces as a
`500`.

If two first uploads of the same reference raced and both published, the
resolver promotes the **oldest live** one and the sweep takes the other, which
is the same file the `409` would have kept.

## Custody after promotion

That permanence is not an omission. Promotion is the handover: from the moment
the function receives the file, how long it lives belongs to the host
application, exactly as with any framework that hands an upload to your code
and then steps back. The sweep reaches only what nobody ever claimed. The
reference is what makes that decision genuinely yours —it never stops
resolving and it never changes underneath you— so a retention policy written
around it holds.

## Why existence belongs to the resolver

The resolver is not the first of two checks; it is the only one. It decides
whether the reference names something this server owns: a bare file name, a
resolved path whose immediate parent is `UPLOADS_DIR`, and a file actually
sitting there —under the bare name, or as a pending one it promotes on the way.
What comes out is a local path that still carries the extension the reference
had, which is what makes `FileHint(extensions=…)` work end to end.

The core repeats none of it. It does not stat, it does not test
`Path.is_file()`, and a path that is not there builds without complaint, so
there is no verdict waiting behind the resolver to catch what it let through.
That is precisely why the rule is written once, on this side, and why the same
resolver serves both execution endpoints and the prefill: the alternative here
is not redundancy, it is a gap.

It also explains the shape of the message. Every rejection on this path is the
resolver's —`File not found: <reference>`, or the storage refusal— and it names
the file by its reference, because that is the only name the client ever knew.

The one value that skips the resolver is a default written in the signature,
since there is nothing to resolve yet; it is checked for belonging to storage
instead, which is what makes it publishable as a reference, and its existence is
settled like everyone else's, on the first execution.

The resolved path is local, and it keeps its extension because storage is a
directory of files. A resolver that returned an opaque key with no extension
(`s3://bucket/key` and the like) would break `FileHint` outright — the core has
nothing but that string to read. FuncToWeb does not have such a resolver, and
this is the assumption anyone writing one would have to keep.

## The author/client border

A path is written in exactly one place, the signature, and it is the one place
where the author is the one writing: the author is the server, knows where
storage is, and is naming a file on the machine the code runs on. Everything on
the client's side of the border —what arrives, what is published, what a
rejection says— is a reference, because the client neither knows nor needs to
know where the file is kept. The signature default is not an exception to the
rule; it is the only sentence spoken on the other side of it, and even that one
is compiled to a reference before the page exists.
