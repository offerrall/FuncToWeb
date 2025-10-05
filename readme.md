# FuncToWeb

**Transform any Python function into a web interface automatically.**

FuncToWeb is a minimalist library that generates web UIs from your Python functions with zero boilerplate. Just add type hints, call `run()`, and you're done.

## Installation

```bash
pip install functoweb
```

## Quick Start

The simplest example possible:

```python
from FuncToWeb import run

def dividir(a: int, b: int):
    return a / b

run(dividir)
```

That's it! Open `http://localhost:8000` and you'll see a form with two integer inputs.

## Adding Constraints

Want to prevent division by zero? Use `IntUi` to add constraints:

```python
from FuncToWeb import run
from FuncToWeb.ui_types import IntUi

def dividir(a: int, b: IntUi(min=1)):
    return a / b

run(dividir)
```

Now `b` must be at least 1. The UI automatically enforces this with HTML5 validation.

## All Available Types

FuncToWeb supports multiple input types with validation:

```python
from FuncToWeb import run
from FuncToWeb.ui_types import IntUi, StrUi, FloatUi, BoolUi

def process_data(
    int_param: IntUi(min=1, max=10),
    list_str_param: list[str] = ["Option 1", "Option 2", "Option 3"],
    str_param: StrUi(min_length=3, max_length=20) = "Hello",
    float_param: FloatUi(min=0.5, max=99.9) = 1.5,
    bool_param: BoolUi() = False
):
    return f"Int: {int_param}, Str: {str_param}, Float: {float_param}, Bool: {bool_param}"

run(process_data)
```

### Type Reference

| Type | Usage | Description |
|------|-------|-------------|
| `int` | `param: int` | Basic integer input |
| `IntUi()` | `param: IntUi(min=0, max=100)` | Integer with constraints |
| `float` | `param: float` | Basic float input |
| `FloatUi()` | `param: FloatUi(min=0.0, max=1.0)` | Float with constraints |
| `str` | `param: str` | Basic string input |
| `StrUi()` | `param: StrUi(min_length=3, max_length=50)` | String with length validation |
| `bool` | `param: bool` | Basic checkbox |
| `BoolUi()` | `param: BoolUi()` | Styled checkbox |
| `list[T]` | `param: list[str] = ["A", "B"]` | Dropdown select (requires default, supports int/float/str/bool) |

## Design Philosophy

FuncToWeb follows these principles:

1. **Pythonic**: Uses native Python syntax (type hints, defaults)
2. **Zero Config**: No decorators, no configuration files, no magic strings
3. **Simple and Customizable**: Clean default UI that can be easily modified
4. **For Internal Tools**: Built for quick internal tools and prototypes, not production apps

## Customizing the UI

The default template is just a starting point. You can easily customize the CSS by modifying the `form.html` file in `FuncToWeb/templates/`. All styles are in a single `<style>` block for easy editing.

## Type Checkers and IDE Support

When using `IntUi()`, `StrUi()`, etc., you might see warnings from type checkers like Pyright:

```python
# pyright: reportInvalidTypeForm=false
from FuncToWeb import run
from FuncToWeb.ui_types import IntUi

def dividir(a: int, b: IntUi(min=1)):  # Pyright warning here
    return a / b

run(dividir)
```

**Why this happens:** Type checkers expect type annotations to be types (like `int`, `str`), but `IntUi(min=1)` is a function call that returns an `Annotated` type.

### Design Decision: Simplicity over Purity

This syntax could have been designed using `Annotated` directly:

```python
from typing import Annotated
from pydantic import Field

def dividir(a: int, b: Annotated[int, Field(ge=1)]):  # Type-safe but verbose
    return a / b
```

**Why FuncToWeb doesn't use this approach:**

FuncToWeb prioritizes **accessibility and simplicity**. The goal is that anyone can create a web interface without knowing about `Annotated`, `Field`, or advanced typing concepts. Compare:

```python
b: IntUi(min=1)                      # Clear, readable, beginner-friendly
b: Annotated[int, Field(ge=1)]       # Requires understanding typing internals
```

Some developers might prefer the pure `Annotated` approach to keep the function "clean" for type checkers. However, FuncToWeb's philosophy is **ease of use first**. The function you write is meant to be a web endpoint wrapper, not production business logic.

**Important note:** Your function remains validated. Under the hood, FuncToWeb uses Pydantic for type conversion and validation where applicable.

**The tradeoff:**
- ❌ You lose autocomplete inside the function (e.g., `b.` won't suggest integer methods)
- ✅ You gain **automatic UI constraints** (HTML5 min/max attributes)
- ✅ You gain **server-side validation** for constrained types
- ✅ You get **simple, readable syntax** that anyone can understand

**Solutions:**

1. **Add the comment** (recommended for simple scripts):
```python
# pyright: reportInvalidTypeForm=false
```

2. **Use `# type: ignore`** on specific lines:
```python
def dividir(a: int, b: IntUi(min=1)):  # type: ignore
    return a / b
```

3. **Stick to basic types** if you don't need constraints:
```python
def dividir(a: int, b: int):  # No warnings, full autocomplete
    return a / b
```

The validation still happens at runtime, so your function **will** receive the correct type even if the IDE doesn't know it.

## Advanced Usage

### Custom Port and Host

```python
run(my_function, host="127.0.0.1", port=5000)
```

### Auto-reload During Development

```python
run(my_function, reload=True)
```

### Default Values

Any parameter with a default value will be pre-filled in the form:

```python
def greet(name: str = "World"):
    return f"Hello, {name}!"
```

## Requirements

- Python 3.10+
- FastAPI
- Pydantic
- Uvicorn

## How It Works

FuncToWeb uses Python's `inspect` module to analyze your function signature, uses Pydantic for type validation, creates FastAPI endpoints, and renders a Jinja2 template with your form.

Validation happens both client-side (HTML5) and server-side.

## License

MIT

## Contributing

Contributions welcome! This project is still young and there's lots of room for new types, better UI components, and more features.