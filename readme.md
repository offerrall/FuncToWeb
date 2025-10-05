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

You can add constraints to your inputs using `Annotated` and `Field` from `typing` and `pydantic` respectively:

```python
from FuncToWeb import run
from typing import Annotated
from pydantic import Field

def dividir(a: int, b: Annotated[int, Field(ge=1)]):
    return a / b

run(dividir)
```

Now `b` must be at least 1. The UI automatically enforces this with HTML5 validation.

## Supported Types

FuncToWeb supports the following Python types out of the box:

- `int` - Integer numbers
- `float` - Decimal numbers
- `str` - Text strings
- `bool` - Checkboxes
- `date` - Date picker (from `datetime`)
- `time` - Time picker (from `datetime`)

## Special Types

FuncToWeb includes pre-configured special types:

### Color
```python
from FuncToWeb import run, Color

def set_theme(primary: Color = "#3b82f6"):
    return f"Theme color: {primary}"

run(set_theme)
```

### Email
```python
from FuncToWeb import run, Email

def subscribe(email: Email):
    return f"Subscribed: {email}"

run(subscribe)
```

## Field Constraints

### Numeric Constraints

```python
from typing import Annotated
from pydantic import Field
from FuncToWeb import run

def create_user(
    age: Annotated[int, Field(ge=18, le=120)],
    height: Annotated[float, Field(gt=0, lt=3.0)]
):
    return f"User: {age} years, {height}m tall"

run(create_user)
```

**Available constraints:**
- `ge` - Greater than or equal to (≥)
- `le` - Less than or equal to (≤)
- `gt` - Greater than (>)
- `lt` - Less than (<)

### String Constraints

```python
from typing import Annotated
from pydantic import Field
from FuncToWeb import run

def register(
    username: Annotated[str, Field(min_length=3, max_length=20)],
    password: Annotated[str, Field(min_length=8)]
):
    return f"User '{username}' registered"

run(register)
```

**Available constraints:**
- `min_length` - Minimum string length
- `max_length` - Maximum string length
- `pattern` - Regex pattern validation

## Literal Types (Dropdowns)

Use `Literal` to create dropdown selects:

```python
from typing import Literal
from FuncToWeb import run

def set_preferences(
    theme: Literal['light', 'dark', 'auto'] = 'auto',
    language: Literal['en', 'es', 'fr'] = 'en'
):
    return f"Theme: {theme}, Language: {language}"

run(set_preferences)
```

## Default Values

Simply set default values in your function signature:

```python
from FuncToWeb import run

def greet(name: str = "World", count: int = 1):
    return f"Hello {name}! " * count

run(greet)
```

## Complete Example

```python
from typing import Annotated, Literal
from pydantic import Field
from datetime import date, time
from FuncToWeb import run, Color, Email

def create_profile(
    name: Annotated[str, Field(min_length=3, max_length=50)] = "John Doe",
    email: Email = "user@example.com",
    event_hour: time = time(14, 30),
    birth_date: date = date(1990, 1, 1),
    color: Color = "#10b981",
    age: Annotated[int, Field(ge=18, le=120)] = 25,
    theme: Literal['light', 'dark', 'auto'] = 'auto',
    newsletter: bool = True
):
    return {
        "name": name,
        "email": email,
        "birth_date": birth_date.isoformat(),
        "event_hour": event_hour.isoformat(),
        "color": color,
        "age": age,
        "theme": theme,
        "newsletter": newsletter
    }

run(create_profile)
```

## Configuration

Customize the server settings:

```python
from FuncToWeb import run

def my_function(x: int):
    return x * 2

run(my_function, host="127.0.0.1", port=5000, template_dir="my_templates")
```

**Parameters:**
- `host` - Server host (default: `"0.0.0.0"`)
- `port` - Server port (default: `8000`)
- `template_dir` - Custom template directory (default: `"templates"`)

## Template Requirements

FuncToWeb requires a `templates/form.html` file. The template receives:

- `title` - Function name (formatted)
- `fields` - List of field configurations

Each field contains:
```python
{
    'name': str,
    'type': str,  # 'text', 'number', 'email', 'color', 'date', 'time', 'checkbox', 'select'
    'default': any,
    'required': bool,
    'options': list,  # For select fields
    'min': int/float,  # For number fields
    'max': int/float,  # For number fields
    'step': str,  # For number fields
    'pattern': str,  # For text fields
    'minlength': int,  # For text fields
    'maxlength': int   # For text fields
}
```

## How It Works

1. **Analysis**: Inspects function signature using `inspect` module
2. **Validation**: Validates type hints and constraints using `pydantic`
3. **Form Generation**: Builds HTML form fields from parameter metadata
4. **Server**: Runs FastAPI server with auto-generated routes
5. **Validation**: Validates submitted data before calling your function

## Error Handling

FuncToWeb validates inputs both client-side (HTML5) and server-side (Pydantic):

```python
from typing import Annotated
from pydantic import Field
from FuncToWeb import run

def divide(
    a: int,
    b: Annotated[int, Field(ge=1)]  # Must be >= 1
):
    return a / b

run(divide)
```

If validation fails, the user sees a clear error message.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Created with ❤️ for developers who want instant UIs for their Python functions.