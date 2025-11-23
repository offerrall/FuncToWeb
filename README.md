# Func To Web 0.8.0

[![PyPI version](https://img.shields.io/pypi/v/func-to-web.svg)](https://pypi.org/project/func-to-web/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-454%20passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **Type hints → Web UI.** Minimal-boilerplate web apps from Python functions.

![func-to-web Demo](docs/images/functoweb.jpg)

## Quick Start (30 seconds)

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

Open `http://127.0.0.1:8000` → **You have a working web app!**

</td>
<td width="50%">

![Demo](docs/images/quick.jpg)

</td>
</tr>
</table>

## Complete Feature Overview

Complete documentation with **examples and screenshots** for each feature:

<table>
<tr>
<td width="50%">

### **Input Types**
- **[Basic Types](https://offerrall.github.io/FuncToWeb/types/)**: `int`, `float`, `str`, `bool`, `date`, `time`
- **[Special Types](https://offerrall.github.io/FuncToWeb/types/)**: `Color`, `Email`
- **[File Uploads](https://offerrall.github.io/FuncToWeb/files/)**: `ImageFile`, `DataFile`, `TextFile`, `DocumentFile`
- **[Dynamic Lists](https://offerrall.github.io/FuncToWeb/lists/)**: `list[Type]` with add/remove buttons
- **[Optional Fields](https://offerrall.github.io/FuncToWeb/optional/)**: `Type | None` with toggle switches
- **[Dropdowns](https://offerrall.github.io/FuncToWeb/dropdowns/)**: Static `Literal['a', 'b']` or Dynamic `Literal[func]`
- **[Validation](https://offerrall.github.io/FuncToWeb/constraints/)**: Pydantic constraints (min/max, regex, list validation)
</td>
<td width="50%">

### **Output Types**
- **[Images & Plots](https://offerrall.github.io/FuncToWeb/images/)**: Return PIL Images and Matplotlib figures
- **[File Downloads](https://offerrall.github.io/FuncToWeb/downloads/)**: Return `FileResponse` for any file type
- **[Multiple Outputs](https://offerrall.github.io/FuncToWeb/multiple-outputs/)**: Return tuples/lists combining text, images, and files

### **Features**
- **[Function Descriptions](https://offerrall.github.io/FuncToWeb/function-descriptions/)**: Display docstrings in the UI
- **[Dark Mode](https://offerrall.github.io/FuncToWeb/dark-mode/)**: Automatic theme switching
- **Large Files**: Optimized streaming (GB+ files)
- **Progress Bars**: Real-time upload/download tracking
- **Error Handling**: Beautiful error messages

</td>
</tr>
</table>

**[Full Documentation](https://offerrall.github.io/FuncToWeb)** 
**[API Reference](https://offerrall.github.io/FuncToWeb/api/)**

## Perfect For

- ✅ **Internal tools** - Give your team GUIs from pure functions
- ✅ **Quick utilities** - Image resize, file convert, data transform, file upload/download...
- ✅ **Testing and Prototyping** - The fastest way to create a web UI

## Quick Examples

Check the [`examples/`](examples/) folder for 14 complete examples (Covers all features)

---

## Requirements

**Core:**
- Python 3.10+
- FastAPI, Uvicorn, Pydantic, Jinja2, python-multipart

**Optional (for examples):**
- Pillow, Matplotlib, Pandas, NumPy

**Development:**
- pytest, mkdocs, mkdocs-material

---

## Run Tests

```bash
pytest tests/ -v
```

## Deploy Docs

```bash
mkdocs gh-deploy
```

[MIT License](LICENSE) • **Made by [Beltrán Offerrall](https://github.com/offerrall)** • Contributions welcome!