# Transform any Python function into a web interface automatically

<div class="grid" markdown>

<div markdown>

```python
from func_to_web import run

# Minimal example
def divide(a: float, b: float):
    return a / b

run(divide)
```

Open `http://127.0.0.1:8000` → **Done!**

- [Input Types](numeric.md) - Learn about supported input types, validation and custom
- [Output Types](outputs.md) - Return files, images, plots, tables...
- [API Endpoint](api_doc.md) - Auto-generated `/doc` for scripts and AI agents
- [Embed Mode](embed.md) - Drop forms into existing sites via iframe
- [Other Features](config.md) - Multiple functions, Authentication, server options...

</div>

<div markdown>

![func-to-web Demo](images/quick.jpg)

</div>

```bash
pip install func-to-web              # Last tagged release from PyPI (recommended)
pip install git+https://github.com/offerrall/FuncToWeb.git   # latest from GitHub (more features, but possibly unstable)

if you find in the docs that a feature is only available in the GitHub version, install from there to use it. Otherwise, the PyPI version is recommended for stability and ease of installation.
```

</div>