# Architecture

FuncToWeb is the top of three layers, each of which solves a different problem.

```text
pytypehint      types, validation, defaults, argument construction
    ↓
pytypehintweb   web plan, browser widgets and transport
    ↓
FuncToWeb       routes, execution, integration and documentation
```

* [`pytypehint`](https://github.com/offerrall/pytypehint) compiles a signature
  into a `Signature`: which types each parameter accepts, which constraints and
  defaults apply, and how the real arguments are built from validated values.
* [`pytypehintweb`](https://github.com/offerrall/pytypehintweb) turns that
  contract into a **plan**: the description of the form that the browser
  consumes, with its JSON transport, plus the widgets that render it.
* FuncToWeb adds what is still missing in order to publish it: the HTTP routes,
  execution, file storage, outputs and `/doc`.

FuncToWeb does not validate on its own, and it does not reinterpret the type
catalog. What it does is re-export that catalog (the constraint and annotation
atoms, `Color`, `Email` and the errors), so whoever writes a function never
needs to import from the lower layers.

## From the function to the response

Each `WebFunction` compiles its schema, its plan and its base HTML once, at
build time. An inconsistent definition fails right there, before the first
request is accepted, rather than in production.

```text
GET /{slug}/       →  base HTML, or an opening with prefill
POST /{slug}/invoke
    → decode()         interprets the transport, and inside it the
                       file_resolver swaps each reference for its local path
    → schema.build()   validates and builds the arguments
    → function
    → return contract (Download or OpenForm, if it declares them)
    → outputs
```

Both execution endpoints share that whole path; the only difference is how the
response travels. See [http.md](http.md) and [streaming.md](streaming.md).

A synchronous function does not run on the event loop but in a thread
(`asyncio.to_thread`): otherwise a blocking call would stall the loop, and with
it every other request the server is handling. See
[streaming.md](streaming.md#async-functions).

The `file_resolver` is the only piece of that path that belongs to FuncToWeb,
and it is the same resolver in both endpoints and in the prefill: `decode()`
decides **where** a file is, walking the structure to any depth, while
FuncToWeb decides **what** counts as a valid file for this server. Neither
layer duplicates the other's work.

## Where it is mounted

A function's page is a complete `.pth-root`: `pytypehintweb` requires that root
for its widgets, and FuncToWeb puts it on the `<body>` rather than on an inner
container, so that page and form are a single surface with a single theme.

The theme belongs to this layer for the same reason: whoever serves the document
is the only one who can settle it before the first paint. `pytypehintweb`
neither chooses nor stores it (it only declares what `data-pth-theme` means),
and the core does not know it exists. See [router.md](router.md#theme) and
[static-assets.md](static-assets.md#theme).

## What counts as public contract

From a `WebFunction` you can read `schema`, `plan` and `html`, plus its
normalized metadata. The plan is also what `/doc` publishes, so a client reads
the same contract the browser consumes. That, together with the names
`func_to_web` exports, is the stable, importable API: the surface you can build
against.

Resolving the return value is not part of that contract.
`WebFunction.return_parser` holds what `Download` and `OpenForm` declared, and
`WebFunctions.forms` holds which function each already-resolved opening jumps
to. Both fields have public names and can be inspected, because the application
needs them, but a public name is not an importable API. Their types,
`ReturnParser` and `FormAction`, and the `has_download()` that queries them,
live in their own modules and are not re-exported from `func_to_web`; neither
are `parser_of()`, `space_of()` or `has_file()`. None of them can be imported
from `func_to_web`, and what the two fields expose is internal state that the
implementation leaves visible, not something published as a contract.

The reason is not the prefix →
[design/architecture.md](design/architecture.md#the-reason-is-not-the-prefix).

Related: [web-function.md](web-function.md), [api-docs.md](api-docs.md),
[types.md](types.md).
