# Limitations

The known limits, gathered in one place. Each one is explained where its
contract lives; this page only lists them.

## Types and validation

| Limit | Where |
| --- | --- |
| Two atoms that would need two different controls do not build together: `Rows`+`Choices`, `Rows`+`IsPassword`, `Slider`+`Placeholder`, `Choices`+`Placeholder` and `Choices`+`Slider` | [types.md](types.md), [design/history-1.6-to-2.0.md](design/history-1.6-to-2.0.md#confirmed-limits-of-the-adapter) |
| The text presentation atoms do not combine with `IsPathFile` (`Str.pattern with IsPathFile is not supported yet`, and the same for `placeholder`, `rows`, `min`, `max`, `choices` and `is_password`), and `Label`/`Description` cannot apply to a list item (`field atoms cannot apply to list items`; `Placeholder` does) | [types.md](types.md), [design/history-1.6-to-2.0.md](design/history-1.6-to-2.0.md#confirmed-limits-of-the-adapter) |
| An `int` outside JavaScript's safe range (±2⁵³−1), and a dataclass with no fields, are a `TypeError` when the plan is compiled | [types.md](types.md), [design/history-1.6-to-2.0.md](design/history-1.6-to-2.0.md#confirmed-limits-of-the-adapter) |
| A recursive dataclass compiles in the core but breaks the plan: `RecursionError` when the `WebFunction` is built | [types.md](types.md), [design/history-1.6-to-2.0.md](design/history-1.6-to-2.0.md#confirmed-limits-of-the-adapter) |

## Prefill and hidden parameters

| Limit | Where |
| --- | --- |
| A prefill travels in the URL, so it stays in the browser history, in `Referer` and in the access log: it is not a place for sensitive data | [prefill.md](prefill.md), [security.md](security.md) |
| There is no other HTTP channel: no POST, no tokens, no prefill stored on the server | [prefill.md](prefill.md) |
| A prefill proposes a value; the user can change it, and `/invoke` accepts any other value | [prefill.md](prefill.md) |
| `hidden` is presentation: it hides the field, it does not lock the value and it does not authorize anything | [prefill.md](prefill.md), [security.md](security.md) |
| The size of a prefill is limited by the browser, the proxies and the server, not by FuncToWeb | [prefill.md](prefill.md) |
| A prefill can preload files, but only ones that are already stored | [prefill.md](prefill.md), [files.md](files.md) |

## `OpenForm`

| Limit | Where |
| --- | --- |
| `OpenForm` can only mark the **whole** return value, and only once: there are no form openings inside a tuple, a list or a union | [open-form.md](open-form.md) |
| It does not combine with `Download` in the same return value, so an execution that uses `OpenForm` produces no other output | [open-form.md](open-form.md) |
| The target function must be registered in the same space, and it is resolved by identity at build time | [open-form.md](open-form.md) |
| Navigation always happens in the same tab, with no modes and no configuration | [open-form.md](open-form.md) |
| It only chains files that are already under `UPLOADS_DIR`; one from outside has no reference, and the execution fails with a `500` | [open-form.md](open-form.md), [files.md](files.md) |

## Files

| Limit | Where |
| --- | --- |
| `max_upload_bytes` is a global per-file ceiling for the whole space, applied by the upload endpoint and never by the constraint declared on a parameter | [files.md](files.md) |
| `IsPathFile(min_size=…, max_size=…)` is caught by the server, and warned about early by the browser only for a file that has just been chosen, so a file that changes size on disk between the page being rendered and the function being called slips through | [files.md](files.md) |
| There is no limit on how many files a request accepts | [files.md](files.md) |
| There is no deduplication by content, no hash and no invalidation: reuse depends on keeping the reference | [files.md](files.md) |
| An upload that no execution or prefill ever uses is eligible for the sweep after `pending_ttl`, one hour by default; `pending_ttl=None` keeps everything | [files.md](files.md) |
| A file that has been used once is never cleaned up: deciding when that goes is the host application's job | [files.md](files.md) |
| `uploads_dir`/`pending_ttl` and `returns_dir`/`returns_ttl` are per process, not per router: the first router that needs a pair settles it, a later one asking for something different gets a `UserWarning`, and two directories, or two TTLs, need two processes | [files.md](files.md), [router.md](router.md) |
| A space with no file fields settles no uploads directory and one with no `Download` settles no returns directory, but both are validated and created when any router is built | [files.md](files.md) |
| The length limit of a reference guards what is written, not what is read: a name already in the storage directory that is longer than the limit still resolves, but it cannot be uploaded | [files.md](files.md) |

## Theme

| Limit | Where |
| --- | --- |
| The theme is chosen by whoever mounts the space, not by the user: no visible selector, no persistence, no cookies and no theme-switching JavaScript | [router.md](router.md#theme) |
| The theme belongs to the whole space: two different themes mean two routers | [router.md](router.md#theme) |
| A host application cannot impose its theme on a page embedded in an iframe: the attribute lives in the `<html>` of that page | [router.md](router.md#theme), [sdk.md](sdk.md#embedding-a-function-page) |

## Results

| Limit | Where |
| --- | --- |
| A plain `list`, `tuple` or `dict` is not rendered as a table: only a pandas or polars `DataFrame` and a 2D numpy array are rendered that way | [outputs.md](outputs.md) |
| Images travel whole inside the response, as a data URI | [outputs.md](outputs.md) |
| A table is rendered in full: no search box, no sorting and no pagination | [outputs.md](outputs.md) |
| A returned file stays available for `returns_ttl`, and is eligible for the sweep afterwards: expiry is applied by the sweep and never on read, and the interval between sweeps is random, so the TTL is a guaranteed minimum lifetime and not a maximum —with the default hour, a file lives between 60 and 120 minutes | [outputs.md](outputs.md), [files.md](files.md#expiry) |
| A download link is for fetching, not for keeping: fetching it fifty times makes it no more permanent than fetching it never | [outputs.md](outputs.md) |
| `returns_ttl` and `pending_ttl` are two settings and not one, so a space can keep its uploads for a week and its downloads for an hour | [router.md](router.md), [files.md](files.md) |
| The sweep of the returns directory deletes only what FuncToWeb wrote there, because that directory lives among other people's files: a name that does not parse is left exactly where it is | [outputs.md](outputs.md) |
| The name declared in a `Download` is shorter than the reference the route validates; a longer one is a `ReturnContractError` before anything is written | [outputs.md](outputs.md) |

## Execution

| Limit | Where |
| --- | --- |
| Streams are not canceled: if the client closes the connection, the function keeps running to the end | [streaming.md](streaming.md) |
| There are no partial results and no explicit progress: while the function runs, only `stdout` travels | [streaming.md](streaming.md) |
| The message of an exception travels to the client as is | [http.md](http.md), [security.md](security.md) |
| The SSE transport polls for pending output every 50 ms: that is the maximum latency of each event, and there is a cost per open connection for as long as the function runs | [streaming.md](streaming.md) |
| `stdout` capture is **experimental**: it replaces `sys.stdout` for the life of the process, so it cannot coexist with another library, or a test harness, that owns it too; turn it off with `capture_prints=False` | [streaming.md](streaming.md), [design/streaming.md](design/streaming.md) |

## Scope

| Limit | Where |
| --- | --- |
| FuncToWeb does not provide authentication, permissions, middleware or CORS: they belong to the host application | [security.md](security.md) |
| There is no configuration model for a space beyond the arguments of `router_of()` and `run()`, and the two variables that name the storage directories, `FUNCTOWEB_UPLOADS_DIR` and `FUNCTOWEB_RETURNS_DIR` | [router.md](router.md), [run.md](run.md) |
| There is no deployment guide: reload, workers, SSL and graceful shutdown belong to whichever server is used | [run.md](run.md) |

