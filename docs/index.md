# FuncToWeb 2.0 documentation

Technical reference for the project. For an overview, see the
[README](../README.md); for hands-on use, see
[`examples/`](../examples/README.md), one capability per file.

## Start here

* [Getting started](getting-started.md) — install, write your first function
  and run it.
* [`run()`](run.md) — the standalone application and the space index.
* [`app_of()`](router.md) — mounting the application in an existing FastAPI host
  application.

## Inputs and forms

* [Types and validation](types.md) — constraints, dataclasses, lists, unions,
  optionals and defaults.
* [Prefill and hidden parameters](prefill.md) — open a form with initial
  values, from Python or from the URL.
* [Files](files.md) — uploads, reusable file references, and which layer
  applies each limit.
* [`WebFunction`](web-function.md) — the name, description and slug of a
  function; prepared spaces.

## Execution and results

* [Execution over HTTP](http.md) — `/invoke`, the request body, the envelope
  and the status codes.
* [Streaming](streaming.md) — `/invoke-stream`, SSE events and `print()`
  capture.
* [Outputs](outputs.md) — text, images, tables and downloads with `Download`.
* [`OpenForm`](open-form.md) — open another function's form with the return
  value as prefill.

## Integration

* [`/doc`](api-docs.md) — the published contract that a client or an agent
  consumes.
* [`sdk.js`](sdk.md) — the helpers that call a space from your own frontend,
  and how to embed a function's page in another site.
* [Static assets](static-assets.md) — `/static`, the icons, the theme and how
  they are cached.
* [Security](security.md) — what FuncToWeb covers and what belongs to the host
  application.

## Internals

* [Architecture](architecture.md) — the layers and what each one solves.
* [Limitations](limitations.md) — the known limits, in a single list.
* [Migrating from 1.6 to 2.0](migration-1.6-to-2.0.md) — what changes, a table
  of equivalences by area, and the upgrade steps.

## Design notes

The pages above say what each thing is: the signature, the values, the errors
and one example. The reasoning behind each of those decisions lives apart, in
[`design/`](design/index.md) — for whoever contributes to FuncToWeb, and for the
curious. Nothing there is needed in order to use the library.
