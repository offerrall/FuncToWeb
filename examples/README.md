# FuncToWeb — Examples

Auto-generated examples covering every feature of FuncToWeb.

## Install

```bash
pip install func-to-web
```

Some examples need optional dependencies:

```bash
pip install pillow matplotlib pandas numpy qrcode pypdf
```

## Run any example

```bash
python 01_basics/01_hello.py
```

Then open http://127.0.0.1:8000

## Folder index

- **`01_basics/`** — Minimal examples of the basic input types: str, int, float, bool, date, time, Color, Email.
- **`02_strings/`** — String input variants: constraints, placeholder, password, textarea, custom pattern message.
- **`03_numeric/`** — Numeric input variants: constraints, step, slider, slider without value label.
- **`04_dropdowns/`** — Dropdowns: Literal, Enum, dynamic (runtime), and dynamic with manual validation.
- **`05_optional/`** — Optional fields with toggle: automatic, explicit (OptionalEnabled/Disabled), and across all types.
- **`06_lists/`** — Dynamic lists: basic, defaults, item constraints, list constraints, combined, list-level labels.
- **`07_files/`** — File uploads: basic, all file types, lists, size limit, persisting uploads.
- **`08_outputs/`** — Output renderers: text, PIL image, plot, table, downloads, multiple outputs, print streaming, errors.
- **`09_composition/`** — Reusable types via Annotated: shared types, layered constraints, lists+optional combos.
- **`10_params/`** — Reusable parameter groups via the Params class.
- **`11_multiple/`** — Multiple functions: list, groups, custom metadata, hidden functions.
- **`12_action_table/`** — Clickable tables that navigate to other functions with prefilled data.
- **`13_auth_config/`** — Authentication, host/port, reverse proxy, custom CSS, and serving a static frontend.
- **`14_recipes/`** — End-to-end recipes: QR generator, PDF merger, file transfer, CSV analyzer, image resize, admin panel, simple CRUD.

## Tip

Every running app exposes a machine-readable API description at `/doc`:

```bash
curl http://127.0.0.1:8000/doc
```
