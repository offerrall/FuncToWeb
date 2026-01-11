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

## Enum Dropdowns

<div class="grid" markdown>

<div markdown>

Use Python `Enum` for reusable dropdowns with named constants:
```python
from enum import Enum
from func_to_web import run

class Theme(Enum):
    LIGHT = 'light'
    DARK = 'dark'
    AUTO = 'auto'

def preferences(theme: Theme):
    # Receives Theme.LIGHT, not just 'light'
    return f"Selected: {theme.name} = {theme.value}"

run(preferences)
```

Your function receives the Enum member with access to both `.name` and `.value`. Useful when the same options are used in multiple functions.

</div>

<div markdown>

![Dropdowns](images/enum_drop.jpg)

</div>

</div>

## Dynamic Dropdowns

<div class="grid" markdown>

<div markdown>

Use `Dropdown()` to generate options dynamically at runtime:
```python
from typing import Annotated
from random import sample
from func_to_web import run
from func_to_web.types import Dropdown

THEMES = ['light', 'dark', 'auto', 'neon', 'retro']

def get_themes():
    """Generate random subset of themes"""
    return sample(THEMES, k=3)

def configure_app(
    theme: Annotated[str, Dropdown(get_themes)]
):
    """Configure app with dynamic dropdown"""
    return f"Selected theme: {theme}"

run(configure_app)
```

The function is called each time the form is rendered, ensuring fresh options every time.

**Legacy syntax (still supported):**
```python
from typing import Literal

def configure_app(
    theme: Literal[get_themes]  # type: ignore
):
    return f"Selected theme: {theme}"
```

This older syntax using `Literal[func]` still works for backwards compatibility, but `Dropdown()` is the recommended approach.

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

## Important: No Server-Side Validation

Dynamic dropdowns **do not validate** the selected value on the server. This is intentional because the available options may change between form render and submission.

**If your application requires security or business logic validation**, you must validate the value yourself in your function:

```python
    def process_action(action: Annotated[str, Dropdown(get_actions)]):
        # ⚠️ Validate the value yourself if security matters
        valid_actions = get_valid_actions_for_current_user()
        if action not in valid_actions:
            raise ValueError(f"Invalid action: {action}")
        
        # Proceed with validated action
        return perform_action(action)
```
    
This differs from static `Literal` types, which **are** validated server-side since the options are fixed.

## What's Next?

You've completed all **Input Types**! Now it's time to learn about adding validation rules.

**Next category:**

- [Types Constraints](constraints.md) - Add validation rules to any type and lists