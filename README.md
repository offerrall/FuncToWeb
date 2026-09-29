# FuncToWeb

**Turn typed Python functions into web interfaces.**

Write a normal Python function with type hints. FuncToWeb turns it into a
ready-to-use web form, validates its input and runs it over HTTP. No models, no
duplicated schemas, no hand-written forms.

The same function is also an HTTP endpoint, a contract published at `/doc` for
people and agents, an application you mount inside FastAPI, and a page your own
frontend opens in a modal.

```python
from func_to_web import run

def divide(a: float, b: float) -> float:
    return a / b  # Any exception becomes a clean error in the page and the API

run(divide)  # http://127.0.0.1:8000
```

The full documentation is at https://offerrall.github.io/func-to-web/.

## Documentation

- [Overview](https://offerrall.github.io/func-to-web/): the same function as a form, an API, a contract and a modal; how it works, what it offers and how it compares.
- [Getting started](https://offerrall.github.io/func-to-web/getting-started/): write your first function and run it.
- [Examples](https://offerrall.github.io/func-to-web/examples/): the runnable examples and mini-apps, how to run them, and what each folder teaches.
- [`run()`](https://offerrall.github.io/func-to-web/run/): the standalone application and the space index.
- [`app_of()`](https://offerrall.github.io/func-to-web/router/): mounting the application in an existing FastAPI host application.
- [Types and validation](https://offerrall.github.io/func-to-web/types/): constraints, dataclasses, lists, unions, optionals and defaults.
- [Prefill and hidden parameters](https://offerrall.github.io/func-to-web/prefill/): open a form with initial values, from Python or from the URL.
- [Files](https://offerrall.github.io/func-to-web/files/): uploads, reusable file references, and which layer applies each limit.
- [`WebFunction` and `WebFunctions`](https://offerrall.github.io/func-to-web/web-function/): the name, description and slug of a function; prepared spaces.
- [Execution over HTTP](https://offerrall.github.io/func-to-web/http/): `/invoke`, the request body, the envelope and the status codes.
- [Streaming](https://offerrall.github.io/func-to-web/streaming/): `/invoke-stream`, SSE events and `print()` capture.
- [Outputs](https://offerrall.github.io/func-to-web/outputs/): text, images, tables and downloads with `Download`.
- [`OpenForm`](https://offerrall.github.io/func-to-web/open-form/): open another function's form with the return value as prefill.
- [`/doc`](https://offerrall.github.io/func-to-web/api-docs/): the published contract that a client or an agent consumes.
- [`sdk.js`](https://offerrall.github.io/func-to-web/sdk/): the helpers that call a space from your own frontend, and how to embed a function's page in another site.
- [Static assets](https://offerrall.github.io/func-to-web/static-assets/): `/static`, the icons, the theme and how they are cached.
- [Security](https://offerrall.github.io/func-to-web/security/): what FuncToWeb covers and what belongs to the host application.
- [Architecture](https://offerrall.github.io/func-to-web/architecture/): the layers and what each one solves.
- [Limitations](https://offerrall.github.io/func-to-web/limitations/): the known limits, in a single list.

### Maintaining

- [The space index](https://offerrall.github.io/func-to-web/design/run/): why the page `run()` adds at `/` navigates with `location.replace()` and carries no form logic of its own.
- [The application](https://offerrall.github.io/func-to-web/design/router/): why both storage TTLs default to one hour, and why the theme is resolved in pure CSS.
- [Prefill: from the query parameter to the plan](https://offerrall.github.io/func-to-web/design/prefill/): what happens between the `prefill` query parameter and the HTML that is served.
- [Files: the upload endpoint, the reference and custody](https://offerrall.github.io/func-to-web/design/files/): why `/upload` does not apply `FileHint.max_size`, why a second upload of the same reference is a `409`, and where custody of a promoted file ends up.
- [`WebFunction` metadata](https://offerrall.github.io/func-to-web/design/web-function/): why the description is passed through `cleandoc()`, and why only the first letter of a displayed name is uppercased.
- [Streaming and print capture](https://offerrall.github.io/func-to-web/design/streaming/): how `print()` capture works, why it is experimental, and why the transport polls.
- [Outputs](https://offerrall.github.io/func-to-web/design/outputs/): why table rows are read with `itertuples()`, why a matplotlib figure is closed, and why a union cannot mix a download with an ordinary branch.
- [The iframe channel: three decisions](https://offerrall.github.io/func-to-web/design/sdk/): why the modal does not close itself by default, why `error` is not about validation, and why the payload of `result` is the envelope of `/invoke` again.
- [Frontend: assets, icons and color](https://offerrall.github.io/func-to-web/design/frontend/): why the content type is decided rather than guessed, why every icon is a file, and why the page adds almost no color of its own.
- [Architecture: what counts as public contract](https://offerrall.github.io/func-to-web/design/architecture/): why the line between the public API and the merely visible internals falls where it does.
- [What changed underneath, from 1.6 to 2.0](https://offerrall.github.io/func-to-web/design/history-1.6-to-2.0/): why 2.0 breaks what it breaks: the two layers underneath were rewritten, and what that widened, lost and left as a limit.
