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

- [Overview](https://offerrall.github.io/func-to-web/): one function as a form, an API, a contract and a modal; how it works.
- [Getting started](https://offerrall.github.io/func-to-web/getting-started/): `run()`, several functions, FastAPI, the options and the examples.
- [Types and validation](https://offerrall.github.io/func-to-web/types/): what a parameter can be, and its constraints.
- [Files](https://offerrall.github.io/func-to-web/files/): file parameters, uploads and how long files are kept.
- [Outputs](https://offerrall.github.io/func-to-web/outputs/): text, tables, images and downloads.
- [Prefill and OpenForm](https://offerrall.github.io/func-to-web/prefill/): forms that open filled in, and functions that open other forms.
- [HTTP API](https://offerrall.github.io/func-to-web/http/): `/invoke`, streaming and `/doc`.
- [`sdk.js`](https://offerrall.github.io/func-to-web/sdk/): calling a space and opening its forms from your own frontend.
- [Security and limits](https://offerrall.github.io/func-to-web/security/): what FuncToWeb guarantees, and what is up to you.
