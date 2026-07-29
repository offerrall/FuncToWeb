# Files: the upload endpoint, the reference and custody

Why `/upload`, the reference and the pending cycle are built the way they are.
The contract — what `IsPathFile` certifies, the rejection and limit tables, the
pending/promoted cycle and the border between path and reference — is in
[files.md](../files.md).

## The two messages of a file default

The two [messages](../files.md#declaring-a-file-default) quote different things,
because they happen at different moments. The first is the core reading the
string as the author typed it, before anything has looked at the disk, so it
echoes that string whole. The second is FuncToWeb turning an already certified
path into the reference it will publish, and by then the directory is the part
that must not travel, so only the name is left.

## Why the endpoint does not apply the field limit

The `IsPathFile` limits belong to the parameter, and `/upload` does **not**
apply them. This is not an oversight:

```text
max_upload_bytes          operational ceiling of the endpoint, cuts early
IsPathFile.min/max_size   parameter constraint, validated on invocation
```

A request to `/upload` carries bytes and a reference. It does not say which
parameter that reference will end up in, and it cannot: the same reference
serves several executions, and inside a list, a union or a nested dataclass
there is no reliable way to point at the node. Applying the field limit there
would mean walking the schema a second time inside FuncToWeb, or trusting a size
declared by the browser. Neither is acceptable.

It is not needed, because the field limit is checked twice without FuncToWeb
taking part:

```text
the browser   weighs the local File before uploading it   (pytypehintweb)
the core      weighs the real file when building          (pytypehint)
```

The first saves the transfer; the second is the verdict, and it is the only one
a hand-written HTTP call cannot skip.

The browser's part is a courtesy, and it works with exactly what it can know: a
freshly chosen `File` carries its `.size`, so it is weighed before anything is
uploaded and, if it is over the limit, no reference is minted and nothing stays
pending (a multiple selection with one bad file is rejected whole, not halfway).
A reference supplied from outside names a file the browser never saw: there is
no size to weigh, none is invented, and the server is not asked for one. A file
edited after being uploaded, an expired reference or a hand-written client all
end up in the same place: the core's measurement.

So the split is:

```text
upload too large for the server         → /upload responds 413
local File that breaks the bound        → the form neither uploads nor sends it
opaque reference that breaks the bound  → /upload accepts it,
                                          /invoke responds 422
file below the field's min_size         → /invoke responds 422
```

The `422` is not a failure of the function: it comes from `schema.build()`,
after the resolver has turned the reference into a path, so the core measures
the real file. It is input validation, with the core's message:

```text
{"error": "SchemaValueError: doc: file too small: 99 bytes, minimum 100"}
```

The same holds inside a list, a dataclass or a union, because `decode()` does
the walking and the core does the measuring.

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

## Why the resolver speaks first

Both check that the file exists, and neither is redundant: the resolver decides
whether the reference names something in the storage directory, and the core
then certifies the path that came out of it. Since the resolver speaks first,
the message you see on this path is the resolver's; the core's
`file does not exist` is left for what does not go through the resolver, such as
a default written in the signature, or for a file that disappears between one
check and the other.

## The author/client border

A path is written in exactly one place, the signature, and it is the one place
where the author is the one writing: the author is the server, knows where
storage is, and is naming a file on the machine the code runs on. Everything on
the client's side of the border —what arrives, what is published, what a
rejection says— is a reference, because the client neither knows nor needs to
know where the file is kept. The signature default is not an exception to the
rule; it is the only sentence spoken on the other side of it, and even that one
is compiled to a reference before the page exists.
