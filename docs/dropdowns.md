# Dropdowns

Use dropdown menus for fixed or dynamic selection options.

## Static Dropdowns

<div class="grid" markdown>

<div markdown>

Use `Literal` for fixed dropdown options:

```python
from typing import Literal
from func_to_web import run

def preferences(
    theme: Literal['light', 'dark', 'auto'],
    language: Literal['en', 'es', 'fr']
):
    return f"Theme: {theme}, Language: {language}"

run(preferences)
```

All options must be literals (strings, numbers, booleans) and all options must be of the same type.

</div>

<div markdown>

![Dropdowns](images/drops_static.jpg)

</div>

</div>

## Dynamic Dropdowns

<div class="grid" markdown>

<div markdown>

Use functions inside `Literal` to generate options dynamically at runtime:

```python
from typing import Literal
from random import sample
from func_to_web import run

THEMES = ['light', 'dark', 'auto', 'neon', 'retro']

def get_themes():
    """Generate random subset of themes"""
    return sample(THEMES, k=3)

def configure_app(
    theme: Literal[get_themes],  # type: ignore
):
    """Configure app with dynamic dropdown"""
    return f"Selected theme: {theme}"

run(configure_app)
```

The `# type: ignore` comment is needed to suppress type checker warnings.

</div>

<div markdown>

![Dynamic Dropdowns](images/drops_dynamic.jpg)

</div>

</div>

## Use Cases for Dynamic Dropdowns

- Load options from a database
- Fetch data from an API
- Generate options based on time or context
- Filter available choices based on business logic

The function is called each time the form is generated, ensuring fresh options every time.

## What's Next?

You've completed all **Input Types**! Now it's time to learn about adding validation rules.

**Next category:**

- [Types Constraints](constraints.md) - Add validation rules to any type and lists