# Streaming and print capture

Why `/invoke-stream` and `print()` capture are built the way they are. The
contract — the events, the `capture_prints` inheritance table and what the
endpoint guarantees — is in [streaming.md](../streaming.md).

## How capture works, and why it is experimental

The first function with capture that runs replaces `sys.stdout` with a
dispatcher: for every write it looks up who it belongs to (the thread that made
it, or the async context), and the write reaches the original `stdout` whether
it was claimed or not. Every other attribute is delegated to the original as is.

```text
at startup       sys.stdout untouched
first capture    sys.stdout = dispatcher over the stdout at that moment
from then on     the dispatcher stays, forever
```

That "forever" is the part worth being honest about: there is no uninstall,
neither when the execution ends nor when the router shuts down. The dispatcher
is transparent, since it always writes to the original and passes on any other
attribute, so in a normal process you do not notice it. Where it does show is
where `stdout` has more than one owner:

| Situation | What happens |
| --- | --- |
| Another library that also wraps `stdout` | It ends up nested with this one, in the order in which they arrived |
| Something **replaces** `sys.stdout` afterwards | Capture is left with no effect |
| Something replaces it beforehand | That object is kept as the original |
| A test harness that swaps `stdout` per test, as pytest does | The output can still go to the object that was there when the dispatcher was installed |

That is why print capture is declared **experimental**: in daily use it works
very well and it is what gives you `print()` on the page, but it is a global
patch, and that is worth knowing. If it gets in your way, turn it off with
`capture_prints=False`: the rest of FuncToWeb does not depend on it. And if you
can, tell us in the repository what happened, because real cases are what will
decide whether this stays as it is.

## Why the transport polls

The transport is not clever on the inside: nothing tells the server that there
is output pending, it goes looking for it. While the function runs, the
generator wakes up every 50 ms, checks whether there is anything to send and
goes back to sleep. Two things follow from that: an event can take up to one
poll to go out, including the final `result`, and every open connection costs
that wake-up for as long as the execution lasts. For what FuncToWeb is, internal
tools with a few users at a time, neither is noticeable.

> Polling will be replaced by direct notification in a future version, to hold
> more simultaneous connections. The contract does not change: the same events,
> the same grouping of printed output and the same final envelope.
