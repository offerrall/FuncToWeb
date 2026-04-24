# Func To Web 1.0.1

[![PyPI version](https://img.shields.io/pypi/v/func-to-web.svg)](https://pypi.org/project/func-to-web/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> Type hints → Web UI. Minimal-boilerplate web apps from Python functions.

![func-to-web Demo](/docs/images/functoweb.jpg)


## Quick start

<table>
<tr>
<td width="50%">

```bash
pip install func-to-web
```

```python
from func_to_web import run

def divide(a: float, b: float):
    return a / b

run(divide)
```

Open `http://127.0.0.1:8000`.

</td>
<td width="50%">

![demo](/docs/images/quick.jpg)

</td>
</tr>
</table>

## Inputs

| Type | Widget | |
|------|--------|-|
| `int`, `float` | Number input with step buttons and optional slider | [docs](docs/numeric.md) |
| `str`, `Email` | Text input, textarea, password, or email | [docs](docs/string.md) |
| `bool` | Toggle switch | [docs](docs/boolean.md) |
| `date`, `time` | Date and time pickers | [docs](docs/datetime.md) |
| `Color` | Hex color picker | [docs](docs/color.md) |
| `File`, `ImageFile`, `VideoFile`, `AudioFile`, `DataFile`, `TextFile`, `DocumentFile` | File upload with extension filter | [docs](docs/files.md) |
| `Literal`, `Enum`, `Dropdown(func)` | Select / dropdown | [docs](docs/dropdown.md) |
| `list[T]` | Dynamic list with add/remove buttons | [docs](docs/lists.md) |
| `T \| None` | Any input with enable/disable toggle | [docs](docs/optional.md) |
| `Params` | Reusable parameter groups | [docs](docs/params.md) |
| `Annotated[T, ...]` | Compose constraints, labels, sliders, placeholders | [docs](docs/composition.md) |

## Outputs

| Return type | Rendered as | |
|-------------|-------------|-|
| `str`, `int`, `float`, `None` | Text with copy button | [docs](docs/outputs.md#text) |
| `PIL Image`, `Matplotlib Figure` | Inline image with expand button | [docs](docs/outputs.md#images) |
| `FileResponse`, `list[FileResponse]` | Download button(s) | [docs](docs/outputs.md#file-downloads) |
| `list[dict]`, `list[tuple]`, `DataFrame`, `ndarray` | Sortable, paginated table with CSV export | [docs](docs/outputs.md#tables) |
| `ActionTable` | Clickable table → next function with prefill | [docs](docs/outputs.md#actiontable) |
| `tuple` / `list` | Multiple outputs combined | [docs](docs/outputs.md#multiple-outputs) |
| `print()` | Streamed to browser in real time | [docs](docs/outputs.md#print-output) |

## Features

- Multiple functions with index page or collapsible groups — [docs](docs/multiple.md)
- URL prefill — forms open prefilled from query params — [docs](docs/url_prefill.md)
- Embed mode — drop any form into an existing site via `?__embed=1` — [docs](docs/embed.md)
- Auto-generated API docs at `/doc` — call your endpoints from scripts or AI agents — [docs](docs/api_doc.md)
- Real-time `print()` output in the browser — [docs](docs/outputs.md#print-output)
- Username/password authentication — [docs](docs/auth.md)
- Dark mode — [docs](docs/dark_mode.md)
- Configurable host, port and path — [docs](docs/config.md)

> Full documentation with examples and screenshots for every feature: **[offerrall.github.io/FuncToWeb](https://offerrall.github.io/FuncToWeb)**

## ActionTable and Params
**`Params`** groups typed parameters into a reusable class. Add a field once, it appears in every function that uses it.

**`ActionTable`** turns a table into navigation — click a row and the next function opens with its form prefilled from that row's data. No routing, no state.

The example below is a full CRUD user database in 70 lines:

```python
import json
from pathlib import Path
from typing import Annotated
from pydantic import Field
from func_to_web import run, ActionTable, HiddenFunction, Params, Email

DB_FILE = Path("users.json")

class UserData(Params):
    name: Annotated[str, Field(min_length=2, max_length=50)]
    email: Email
    phone: Annotated[str, Field(pattern=r'^\+?[0-9]{9,15}$')]

def _load() -> dict:
    if not DB_FILE.exists():
        return {}
    return {int(k): v for k, v in json.loads(DB_FILE.read_text()).items()}

def _save(db: dict):
    DB_FILE.write_text(json.dumps(db, indent=2))

def _check(db: dict, id: int):
    if id not in db:
        raise ValueError(f"User {id} not found")

def _user_dict(uid: int, data: UserData) -> dict:
    return {"id": uid, **vars(data)}

def edit_users():
    """Edit users"""
    return ActionTable(data=_load, action=edit_user)

def delete_users():
    """Delete users"""
    return ActionTable(data=_load, action=delete_user)

def create_user(data: UserData):
    """Create a new user"""
    db = _load()
    uid = max(db) + 1 if db else 1
    db[uid] = _user_dict(uid, data)
    _save(db)
    return f"User {uid} created"

def edit_user(id: int, data: UserData):
    """Edit an existing user"""
    db = _load()
    _check(db, id)
    db[id] = _user_dict(id, data)
    _save(db)
    return f"User {id} updated"

def delete_user(id: int):
    """Delete a user"""
    db = _load()
    _check(db, id)
    del db[id]
    _save(db)
    return f"User {id} deleted"

run([edit_users, delete_users, create_user, HiddenFunction(delete_user), HiddenFunction(edit_user)])
```

![Demo](/docs/images/crud_1.jpg)

`UserData` is the single source of truth. Swap the JSON file for SQLAlchemy and you have a production-ready CRUD in a few more lines.

> `ActionTable` is experimental. Simple types (str, int, float) work well. Files are not yet supported via row navigation.

## Using Func To Web alongside your frontend

Three building blocks let you plug FuncToWeb into anything you already have:

- **URL prefill** — every function lives at its own URL and accepts query params, so you can deep-link to a form already filled in.
- **Embed mode** — append `?__embed=1` and the page renders without sidebar, theme toggle or chrome, with a transparent background. Drop it in an `<iframe>` and it blends into the parent site.
- **`/doc` endpoint** — every app exposes a plain-text, machine-readable doc listing every endpoint with its parameters, constraints, and a working `curl`. Scripts, agents and LLMs can call your functions without prior knowledge of the app.

Together these turn each function into a self-contained, embeddable, scriptable operation: edit a record, upload and process files, generate a report, run a bulk action — from your own UI, from a CLI, or from an AI agent.

## Call from code or AI agents

Every app exposes a plain-text doc at `/doc` with all endpoints, parameters and a working curl example for each one:

```bash
curl http://127.0.0.1:8000/doc
```

Any HTTP client, script or LLM can read it and call your functions — no SDK, no protocol, just HTTP.

## Examples

### File transfer

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

### Protected admin panel

```python
import subprocess
from typing import Literal
from func_to_web import run

def restart_service(service: Literal['nginx', 'gunicorn', 'celery']):
    subprocess.run(["sudo", "supervisorctl", "restart", service], check=True)
    return f"{service} restarted."

run(restart_service, auth={"admin": "your_password"})
# Use HTTPS in production.
```

### QR code generator

```python
import qrcode
from func_to_web import run

def make_qr(text: str):
    return qrcode.make(text).get_image()

run(make_qr)
```

### PDF merger

```python
from io import BytesIO
from pypdf import PdfWriter
from func_to_web import run
from func_to_web.types import DocumentFile, FileResponse

def merge_pdfs(files: list[DocumentFile]):
    merger = PdfWriter()
    for pdf in files:
        merger.append(pdf)
    output = BytesIO()
    merger.write(output)
    return FileResponse(data=output.getvalue(), filename="merged.pdf")

run(merge_pdfs)
```

More in [`examples/`](examples/) and [`examples/apps/`](examples/apps/).

---

## Requirements

**External:**
- Python 3.10+
- FastAPI, Uvicorn, Jinja2, python-multipart, itsdangerous, aiofiles, starlette

**Internal:**
- [pytypeinput](https://github.com/offerrall/pytypeinput) — type analysis engine (2030+ tests). Powers Func To Web's type system and can be used standalone to build other interfaces — a CLI, a Qt app, or anything else.
- [pytypeinputweb](https://github.com/offerrall/pytypeinputweb) — JS/CSS form renderer built on pytypeinput.

**Optional (for specific features):**
- Pillow, Matplotlib, Pandas, NumPy, Polars

---


400 stars and Awesome Python — didn't see that coming at all. Built this to scratch my own itch, so genuinely thanks.

I want to keep making it better and I'd love to hear how you actually use it, what's missing, what's annoying. If there's demand I'll open a Discord, otherwise issues work fine. Any help — code, docs, bug reports — is very welcome.

[MIT License](LICENSE) · Made by [Beltrán Offerrall](https://github.com/offerrall) · Contributions welcome