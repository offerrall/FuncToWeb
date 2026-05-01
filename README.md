# Func To Web 1.0.1

[![PyPI version](https://img.shields.io/pypi/v/func-to-web.svg)](https://pypi.org/project/func-to-web/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> Type hints → Web UI. Minimal-boilerplate web apps from Python functions.

![func-to-web Demo](/docs/images/functoweb.jpg)

One typed Python function → form + iframe + HTTP endpoint, simultaneously. Three ways to use it:

- **Standalone** — internal tools, admin panels, scripts. The auto-generated UI is the app.
- **Embedded** — drop forms into existing sites via `<iframe>` with URL prefill. "Export to PDF" buttons, CSV importers, modal editors.
- **Backend for your own SPA** — mount your React/Vue/Svelte bundle alongside; call functions over HTTP or iframe them where it's faster. One process, no CORS, no separate deploy.

Validation, file uploads, SSE streaming and downloads come wired in. You write the function; routes and forms are not your problem.

## Quick start

```bash
pip install func-to-web
```

```python
from func_to_web import run

def divide(a: float, b: float):
    return a / b

run(divide)
```

Open `http://127.0.0.1:8000`. Done.

**Full docs with examples and screenshots:** [offerrall.github.io/FuncToWeb](https://offerrall.github.io/FuncToWeb)

## Inputs

| Type | Widget | Docs |
|------|--------|------|
| `int`, `float` | Number / slider | [→](docs/numeric.md) |
| `str`, `Email` | Text / textarea / password | [→](docs/string.md) |
| `bool` | Toggle | [→](docs/boolean.md) |
| `date`, `time` | Pickers | [→](docs/datetime.md) |
| `Color` | Hex picker | [→](docs/color.md) |
| `File`, `ImageFile`, `VideoFile`, ... | Upload | [→](docs/files.md) |
| `Literal`, `Enum`, `Dropdown(func)` | Select | [→](docs/dropdown.md) |
| `list[T]` | Dynamic list | [→](docs/lists.md) |
| `T \| None` | Toggle + input | [→](docs/optional.md) |
| `Params` | Reusable groups | [→](docs/params.md) |
| `Annotated[T, ...]` | Constraints, labels, sliders | [→](docs/composition.md) |

## Outputs

| Return type | Rendered as | Docs |
|-------------|-------------|------|
| `str`, `int`, `float`, `None` | Text + copy button | [→](docs/outputs.md#text) |
| `PIL Image`, `Matplotlib Figure` | Inline image | [→](docs/outputs.md#images) |
| `FileResponse` | Download button | [→](docs/outputs.md#file-downloads) |
| `DataFrame`, `list[dict]`, ... | Sortable table + CSV | [→](docs/outputs.md#tables) |
| `ActionTable` | Clickable rows → next function | [→](docs/outputs.md#actiontable) |
| `tuple` / `list` | Multiple outputs | [→](docs/outputs.md#multiple-outputs) |
| `print()` | Streamed live | [→](docs/outputs.md#print-output) |

## Features

- **Multiple functions** with index page or groups — [docs](docs/multiple.md)
- **URL prefill** — open forms with values from query params — [docs](docs/url_prefill.md)
- **Embed mode** — drop any form into your site via `?__embed=1` — [docs](docs/embed.md)
- **Auto-generated API docs** at `/doc` for scripts and AI agents — [docs](docs/api_doc.md)
- **Authentication** with username/password — [docs](docs/auth.md)
- **Dark mode** — [docs](docs/dark_mode.md)
- **Server config** — host, port, reverse proxy — [docs](docs/config.md)

## Examples

**File transfer**

```python
from func_to_web import run, File
import shutil, os

downloads = os.path.expanduser("~/Downloads")

def upload_files(files: list[File]):
    for f in files:
        shutil.move(f, downloads)
    return "Done."

run(upload_files)
```

**QR code generator**

```python
import qrcode
from func_to_web import run

def make_qr(text: str):
    return qrcode.make(text).get_image()

run(make_qr)
```

**Protected admin panel**

```python
import subprocess
from typing import Literal
from func_to_web import run

def restart_service(service: Literal['nginx', 'gunicorn', 'celery']):
    subprocess.run(["sudo", "supervisorctl", "restart", service], check=True)
    return f"{service} restarted."

run(restart_service, auth={"admin": "your_password"})
```

More in [`examples/`](examples/) — including a full [CRUD app in 70 lines](examples/14_recipes/simple_crud.py) using `Params` + `ActionTable`.

## Install

```bash
pip install func-to-web                                     # stable
pip install git+https://github.com/offerrall/FuncToWeb.git  # latest
```

**Requirements:** Python 3.10+. Core deps installed automatically; Pillow, Matplotlib, Pandas, NumPy and Polars are optional.

Built on [pytypeinput](https://github.com/offerrall/pytypeinput) and [pytypeinputweb](https://github.com/offerrall/pytypeinputweb), usable standalone for CLIs, Qt apps, etc.

Feedback, issues and contributions welcome — they keep the project moving.

[MIT License](LICENSE) · Made by [Beltrán Offerrall](https://github.com/offerrall)