# Dark Mode

FuncToWeb includes built-in dark mode. Click the 🌙/☀️ button in the top-right corner to toggle — the preference is saved in the browser automatically.

No configuration needed. Works on all pages out of the box.

## Customizing Colors

Override CSS variables to customize the look for both themes:

```python
from func_to_web import run

run(
    my_function,
    css_vars={
        "--functoweb-submit-bg-light": "#10b981",
        "--functoweb-submit-bg-dark":  "#059669",
    }
)
```

Use `list_css_variables()` from `pytypeinputweb` to see all available variables:

```python
from pytypeinputweb import list_css_variables

for name, value in list_css_variables().items():
    print(f"{name}: {value}")
```