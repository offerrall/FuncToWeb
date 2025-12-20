# Func To Web 0.9.8

[![PyPI version](https://img.shields.io/pypi/v/func-to-web.svg)](https://pypi.org/project/func-to-web/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-514%20passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **Type hints → Web UI.** Minimal-boilerplate web apps from Python functions.

![func-to-web Demo](https://raw.githubusercontent.com/offerrall/FuncToWeb/refs/heads/main/docs/images/functoweb.jpg)

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

![Demo](https://raw.githubusercontent.com/offerrall/FuncToWeb/refs/heads/main/docs/images/quick.jpg)

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
- **[File Uploads](https://offerrall.github.io/FuncToWeb/files/)**: `File`, `ImageFile`, `DataFile`, `TextFile`, `DocumentFile`
- **[Dynamic Lists](https://offerrall.github.io/FuncToWeb/lists/)**: `list[Type]` with add/remove buttons
- **[Optional Fields](https://offerrall.github.io/FuncToWeb/optional/)**: `Type | None` with toggle switches
- **[Dropdowns](https://offerrall.github.io/FuncToWeb/dropdowns/)**: Static (`Literal`, `Enum`) or Dynamic (`Literal[func]`)
- **[Validation](https://offerrall.github.io/FuncToWeb/constraints/)**: Pydantic constraints (min/max, regex, list validation)
</td>
<td width="50%">

### **Output Types**
- **[Images & Plots](https://offerrall.github.io/FuncToWeb/images/)**: Return PIL Images and Matplotlib figures
- **[File Downloads](https://offerrall.github.io/FuncToWeb/downloads/)**: Return `FileResponse` for any file type
- **[Tables](https://offerrall.github.io/FuncToWeb/tables/)**: Return `list[dict]`, `list[tuple]`, Pandas, NumPy, or Polars DataFrames
- **[Multiple Outputs](https://offerrall.github.io/FuncToWeb/multiple-outputs/)**: Return tuples/lists combining text, images, tables, and files

### **Features**
- **[Authentication](https://offerrall.github.io/FuncToWeb/authentication/)**: Username/password protection
- **[Function Descriptions](https://offerrall.github.io/FuncToWeb/function-descriptions/)**: Display docstrings in the UI
- **[Dark Mode](https://offerrall.github.io/FuncToWeb/dark-mode/)**: Automatic theme switching
- **[Server Options](https://offerrall.github.io/FuncToWeb/server-configuration/)**: Custom host, port, path and more
- **Large Files**: Optimized streaming (GB+ files)
- **Progress Bars**: Real-time upload/download tracking
- **Error Handling**: Beautiful error messages

</td>
</tr>
</table>

**[Full Documentation](https://offerrall.github.io/FuncToWeb)** 
**[API Reference](https://offerrall.github.io/FuncToWeb/api/)**

## Perfect For

- ✅ **Rapid Prototyping** - From pure Python function to usable web interface in seconds.
- ✅ **Image Processing** - Upload, process, and download images with PIL/Pillow.
- ✅ **Data Science & Reporting** - Instantly publish Pandas/Polars DataFrames and matplotlib plots without frontend code.
- ✅ **High-Performance File Transfer** - Stream uploads and downloads at native network/disk speeds. Handles massive files efficiently with minimal memory footprint.
- ✅ **Secure Internal Apps** - Admin panels, dashboards, and team tools protected by built-in authentication.

## Quick Examples

### DIY AirDrop / LocalSend (Very Fast File Transfers)

```python
from pathlib import Path
from func_to_web import run
from func_to_web.types import File

desktop_path = Path.home() / "Desktop"

def upload_files(
    files: list[File],
): 
    for f in files:
        print(f"Uploaded file: {f}")
    return "Files uploaded successfully!"

run(upload_files, auto_delete_uploads=False, uploads_dir=desktop_path)
```

### Secure Admin Panel
Protect sensitive tools with built-in authentication in one line.

```python
import subprocess
from typing import Literal
from func_to_web import run

# 🔒 MANDATORY: Use HTTPS (Nginx).

def restart_service(service: Literal['nginx', 'gunicorn', 'celery']):
    """Restarts a system service."""
    # check=True raises an error shown in the Web UI if the command fails
    subprocess.run(["sudo", "supervisorctl", "restart", service], check=True)
    return f"✅ Service {service} restarted."

run(restart_service, auth={"admin": "super_secret_password"})
```

### QR Code Generator
Generate QR codes instantly from text.

```python
import qrcode
from func_to_web import run

def make_qr(text: str):
    """Returns a QR code image for the given text."""
    return qrcode.make(text).get_image()

run(make_qr)
```

### PDF Merger
Merge multiple PDF files into a single document instantly.

```python
from io import BytesIO
from pypdf import PdfWriter
from func_to_web import run
from func_to_web.types import DocumentFile, FileResponse

def merge_pdfs(files: list[DocumentFile]):
    """Upload PDFs and get a single merged file back."""
    merger = PdfWriter()
    for pdf in files:
        merger.append(pdf)

    output = BytesIO()
    merger.write(output)
    
    return FileResponse(data=output.getvalue(), filename="merged.pdf")

run(merge_pdfs)
```

Check the [`examples/`](examples/) folder for +20 complete examples (Covers all features)

## Requirements

**Core:**
- Python 3.10+
- FastAPI, Uvicorn, Pydantic, Jinja2, python-multipart, itsdangerous

**Optional (for extended functionality):**
- Pillow, Matplotlib, Pandas, NumPy, Polars

**Development:**
- pytest, mkdocs, mkdocs-material

## Run Tests

```bash
pytest tests/ -v
```

[MIT License](LICENSE) • **Made by [Beltrán Offerrall](https://github.com/offerrall)** • Contributions welcome!