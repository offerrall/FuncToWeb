# Func To Web 0.7.3

[![GitHub stars](https://img.shields.io/github/stars/yourusername/func-to-web?style=social)](https://github.com/offerrall/FuncToWeb/stargazers)
[![PyPI version](https://img.shields.io/pypi/v/func-to-web.svg)](https://pypi.org/project/func-to-web/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-454%20passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **Transform any Python function into a complete web app automatically.** Just type hints and `run()`.

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

def divide(a: int, b: int):
    return a / b

run(divide)
```

Open `http://127.0.0.1:8000` → **You have a working web app!**

</td>
<td width="50%">

![Demo](docs/images/quick.jpeg)

</td>
</tr>
</table>

---

## Complete Feature Overview

Complete documentation with examples and screenshots for each feature:

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

</td>
<td width="50%">

### **Features**
- **[Validation](https://offerrall.github.io/FuncToWeb/constraints/)**: Pydantic constraints (min/max, regex, list validation)
- **[Images & Plots](https://offerrall.github.io/FuncToWeb/images/)**: Return PIL Images and Matplotlib figures
- **[File Downloads](https://offerrall.github.io/FuncToWeb/downloads/)**: Return `FileResponse` for any file type
- **[Multiple Functions](https://offerrall.github.io/FuncToWeb/multiple/)**: Auto-generated index page
- **[Dark Mode](https://offerrall.github.io/FuncToWeb/dark-mode/)**: Automatic theme switching
- **Large Files**: Optimized streaming (GB+ files)
- **Progress Bars**: Real-time upload/download tracking
- **Error Handling**: Beautiful error messages

</td>
</tr>
</table>

---

**[Full Documentation](https://offerrall.github.io/FuncToWeb)** 

---

## Quick Examples

Check the [`examples/`](examples/) folder for 20+ complete examples:

```bash
python examples/01_basic_division.py
python examples/08_image_blur.py
python examples/15_multiple_tools.py
python examples/20_lists_limits.py
```

---

## Requirements

- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic
- Jinja2
- python-multipart

Optional for examples:
- Pillow (for image processing)
- Matplotlib (for plots)
- NumPy (for numerical computations)

Development dependencies:
- pytest (for running tests)

---

[MIT License](LICENSE) • **Made by [Beltrán Offerrall](https://github.com/offerrall)** • Contributions welcome!