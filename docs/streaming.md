# Streaming

`POST /{slug}/invoke-stream` runs the same function as
[`/invoke`](http.md) and streams over SSE whatever it prints while it runs.

```text
/invoke          waits, returns JSON     scripts, services, agents
/invoke-stream   streams, then returns   the FuncToWeb interface
```

It does not replace `/invoke`: it accepts the same body, shares the whole
execution and ends with the same envelope. Only the transport changes, which is
why [`/doc`](api-docs.md) names it in one line instead of describing it: the
transport detail belongs in this document.

## The events

```text
POST /{slug}/invoke-stream
Content-Type: application/json
Accept: text/event-stream
```

```text
event: start
data: {}

event: print
data: {"text": "Working...\n"}

event: result
data: {"result": {"type": "text", "value": "Done"}}
```

* `start` arrives once, at the beginning;
* `print` arrives **zero or more times**, carrying whatever the function has
  written to `stdout` since the previous event;
* `result` arrives exactly once, at the end, with `{"result": …}` or
  `{"error": …}`.

A function that prints nothing emits only `start` and `result`: the endpoint
exists for every function.

The HTTP status is always `200`, even when the function fails, because the
response has already started; the error travels inside `result`. The response
goes out with `Cache-Control: no-cache` and `X-Accel-Buffering: no`, so a proxy
in front does not buffer the events.

The text travels **as is**: line breaks, empty lines and fragments without a
trailing newline are all preserved. What gets grouped into a single event is
whatever was written between two reads, so one `print` event can carry several
lines and one line can be split across two events. A client that displays it
must concatenate, not treat each event as a line.

What the function prints **also** keeps appearing in the server console: print
capture observes `stdout`; it does not hijack it.

## Turning capture off

Capture is turned off per function or per space:

```python
router_of(
    [
        normal_task,
        WebFunction(noisy_task, capture_prints=False),
    ],
    capture_prints=True,
)
```

```text
WebFunction.capture_prints set        → wins
WebFunction.capture_prints not set    → inherits from router/run
router/run not set                    → True
```

That is why the field is `bool | None`: `None` means "inherit", not
"disabled".

Turning it off does **not** remove the route: `/invoke-stream` still exists and
still emits `start` and `result`, with no `print` events. It is execution
policy, so it does not appear in the schema, in the plan or in `/doc`, and as
long as no function with capture runs, `sys.stdout` is not replaced.

Every execution has its own capture, resolved by the thread that runs the
function or by the async context it lives in. Two simultaneous executions do not
mix their output.

## Capture is experimental

The first function with capture that runs replaces `sys.stdout` with a
dispatcher, and there is no uninstall: the replacement is global and it stays
for the life of the process. It is transparent, since it always writes to the
original and passes on any other attribute, so in a normal process you do not
notice it. Where it does show is where `stdout` has more than one owner — a test
harness that swaps `stdout` per test, as pytest does, is the usual case.

If it gets in your way, turn it off with `capture_prints=False`: the rest of
FuncToWeb does not depend on it.

How the dispatcher works, and why that makes capture experimental, is the
longest piece of reasoning in these docs →
[design/streaming.md](design/streaming.md).

## `async` functions

Both endpoints accept a plain function or an `async def`, with no metadata
needed to declare which it is: the decision is made with
`inspect.iscoroutinefunction()`. A synchronous function runs in a separate
thread (`asyncio.to_thread`), so a blocking function does not stall the server
or other requests.

## In the web interface

The page uses `fetch()` with POST, not `EventSource`, which only supports GET.
While the function runs, the page shows a status block and accumulates `stdout`
in a single `<pre>`, written as text and never as HTML. When `result` arrives,
it renders the outputs, or the error, below what was printed.

### What printing a lot looks like

A function that prints in a loop would otherwise push the rest of the page —the
result, the form, the button— further down with every line. It does not: what
was printed gets a window of about ten lines and scrolls inside it, and the page
keeps its shape however long the run is.

The window **follows the output** while you are at the bottom of it, so the last
line printed is the one on screen, including when the run ends. Scroll up and it
stops following, because you are reading; come back to the bottom and it follows
again. Nothing about this is configurable from Python, but the height is a CSS
variable, so a page that wants more room says so:

```css
:root { --ftw-stdout-max-height: 30rem; }
```

The page also keeps a **bounded** amount of text — the last 40,000 characters,
some hundreds of lines. A loop printing without end would otherwise grow one
string until the tab stops answering, which is a page that has crashed rather
than a page showing a long run. When something has been dropped, the box says
so on its first line:

```text
… earlier output trimmed
```

This is what the *page* keeps, not what the endpoint sends: every `print` event
still carries everything the function wrote, and a client of your own that wants
the whole output has it. What the server holds is unbounded too, so a function
that prints hundreds of megabytes still costs what it costs on the way out —
the limit here is what the browser is asked to hold on to.

Because the transport is a stream parsed by hand, the client reassembles the
events: an `event:` line, one or more `data:` lines and the blank line that
closes them. It tolerates `CRLF` and an event split across two reads, because
nothing guarantees that a network chunk lines up with an event.

A stream that is cut before `result`, invalid JSON or a response that is not a
stream are all shown as `Invalid server response`: it is a protocol error, not a
function error.

## What it does not do

There is no cancellation: if the client closes the connection, the function
keeps running to the end. There are no partial results and no explicit progress:
what you see is what the function prints. See
[limitations.md](limitations.md).

While the function runs, the generator wakes up every 50 ms, checks whether
there is anything to send and goes back to sleep:

| Cost | What it means |
| --- | --- |
| Latency | An event can take up to one poll to go out, including the final `result` |
| Connections | Every open connection costs that wake-up for as long as the execution lasts |

Why the transport polls instead of being notified, and what will replace it, is
reasoning rather than contract →
[design/streaming.md](design/streaming.md#why-the-transport-polls).

Related: [http.md](http.md), [outputs.md](outputs.md), [router.md](router.md).
