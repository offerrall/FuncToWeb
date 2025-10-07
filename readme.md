# Func To Web 0.2.0

**Transform any Python function into a web interface automatically.**

func-to-web is a minimalist library that generates web UIs from your Python functions with zero boilerplate. Just add type hints, call `run()`, and you're done.

Simple, powerful, and easy to understand.

![func-to-web Demo](images/functoweb.jpg)

## Quick Start (Minimal Example)

```python
from func_to_web import run

def divide(a: int, b: int):
    return a / b

run(divide)
```

Open `http://127.0.0.1:8000` in your browser and you'll see an auto-generated form.

![func-to-web Demo](images/demo.jpg)


## Installation

```bash
pip install func-to-web
```

## Examples

**Check the `examples/` folder** for 15+ complete, runnable examples covering everything from basic forms to image processing and data visualization. Each example is a single Python file you can run immediately:

```bash
python examples/01_basic_division.py
python examples/08_image_blur.py
python examples/11_plot_sine.py
```

![Examples Preview](images/full_example.jpeg)

## What Can You Do?

### Basic Types

All Python built-in types work out of the box:

```python
from func_to_web import run
from datetime import date, time

def example(
    text: str,              # Text input
    number: int,            # Integer input
    decimal: float,         # Decimal input
    checkbox: bool,         # Checkbox
    birthday: date,         # Date picker
    meeting: time           # Time picker
):
    return "All basic types supported!"

run(example)
```

![Basic Types](images/basic.jpg)

### Special Input Types

```python
from func_to_web import run, Color, Email

def special_inputs(
    favorite_color: Color,  # Color picker
    contact: Email          # Email validation
):
    return f"Color: {favorite_color}, Email: {contact}"

run(special_inputs)
```

![Color Picker](images/color.jpg)

### File Uploads

```python
from func_to_web import run, ImageFile, DataFile, TextFile, DocumentFile

def process_files(
    photo: ImageFile,       # .png, .jpg, .jpeg, .gif, .webp
    data: DataFile,         # .csv, .xlsx, .xls, .json
    notes: TextFile,        # .txt, .md, .log
    report: DocumentFile,   # .pdf, .doc, .docx
):
    return "Files uploaded!"

run(process_files)
```

![File Upload](images/files.jpg)

### Dropdowns (Static)

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

![Dropdowns](images/drop.jpg)

All options must be literals (strings, numbers, booleans) and all options must be of the same type.

### Dropdowns (Dynamic)

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

**Use cases for dynamic dropdowns:**
- Load options from a database
- Fetch data from an API
- Generate options based on time or context
- Filter available choices based on business logic

The function is called each time the form is generated, ensuring fresh options every time. The `# type: ignore` comment is needed to suppress type checker warnings, the 15_dynamic_dropdown.py example demonstrates this.

### Constraints & Validation

```python
from typing import Annotated
from pydantic import Field
from func_to_web import run

def register(
    age: Annotated[int, Field(ge=18, le=120)],              # Min/max values
    username: Annotated[str, Field(min_length=3, max_length=20)],  # Length limits
    rating: Annotated[float, Field(gt=0, lt=5)]             # Exclusive bounds
):
    return f"User {username}, age {age}, rating {rating}"

run(register)
```

![Validation](images/limits.jpg)

### Return Images & Plots

func-to-web automatically detects and displays images from PIL/Pillow and matplotlib:

```python
from func_to_web import run, ImageFile
from PIL import Image, ImageFilter

def blur_image(image: ImageFile, radius: int = 5):
    img = Image.open(image)
    return img.filter(ImageFilter.GaussianBlur(radius))

run(blur_image)
```

![Image Processing](images/image.jpg)

```python
from func_to_web import run
import matplotlib.pyplot as plt
import numpy as np

def plot_sine(frequency: float = 1.0, amplitude: float = 1.0):
    x = np.linspace(0, 10, 1000)
    y = amplitude * np.sin(frequency * x)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y)
    ax.grid(True)
    return fig

run(plot_sine)
```

![Plot Result](images/plot.jpg)

## Run Multiple Functions 

You can serve multiple functions simultaneously. When passing a list of functions, func-to-web automatically creates a responsive index page where users can select the tool they want to use. This is demonstrated in Example 15.

```python
from func_to_web import run

def calculate_bmi(weight_kg: float, height_m: float):
    """Calculate Body Mass Index"""
    bmi = weight_kg / (height_m ** 2)
    return f"BMI: {bmi:.2f}"

def celsius_to_fahrenheit(celsius: float):
    """Convert Celsius to Fahrenheit"""
    fahrenheit = (celsius * 9/5) + 32
    return f"{celsius}°C = {fahrenheit}°F"

def reverse_text(text: str):
    """Reverse a string"""
    return text[::-1]

# Pass a list of functions to create an index page
run([calculate_bmi, celsius_to_fahrenheit, reverse_text])
```

![Multiple Tools](images/multiple.jpg)

## Features

### Input Types
- `int`, `float`, `str`, `bool` - Basic types
- `date`, `time` - Date and time pickers
- `Color` - Color picker with preview
- `Email` - Email validation
- `Literal[...]` - Dropdown selections, static or dynamic
- `ImageFile`, `DataFile`, `TextFile`, `DocumentFile` - File uploads

### Validation
- **Numeric**: `ge`, `le`, `gt`, `lt` (min/max bounds)
- **String**: `min_length`, `max_length`, `pattern` (regex)
- **Required/Optional**: Automatic detection from type hints
- **Default values**: Set in function signature

### Output Types
- **Text/Numbers/Dicts** - Formatted as JSON
- **PIL Images** - Displayed as images
- **Matplotlib Figures** - Rendered as PNG
- **Any object** - Converted with `str()`

## Configuration

### One function:
```python
from func_to_web import run

def my_function(x: int):
    return x * 2

run(my_function, host="127.0.0.1", port=5000, template_dir="my_templates")
```

### Multiple functions:
```python
from func_to_web import run

def func1(x: int): 
    return x * 2

def func2(y: str): 
    return y.upper()

run([func1, func2], host="127.0.0.1", port=5000, template_dir="my_templates")
```

**Parameters:**
- `func_or_list` - Single function or list of functions to serve
- `host` - Server host (default: `"0.0.0.0"`)
- `port` - Server port (default: `8000`)
- `template_dir` - Custom template directory (optional)

## Why func-to-web?

- **Minimalist** - Under 1500 lines total, backend + frontend + docs
- **Zero boilerplate** - Just type hints and you're done
- **Powerful** - Supports all common input types including files
- **Smart output** - Automatically displays images, plots, and data
- **Type-safe** - Full Pydantic validation
- **Client + server validation** - Instant feedback and robust checks
- **Batteries included** - 15+ examples in the `examples/` folder
- **Multi-function support** - Serve multiple tools from one server

## How It Works

1. **Analysis** - Inspects function signature using `inspect`
2. **Validation** - Validates type hints and constraints using `pydantic`
3. **Form Generation** - Builds HTML form fields from metadata
4. **File Handling** - Saves uploaded files to temp locations
5. **Server** - Runs FastAPI server with auto-generated routes
6. **Result Processing** - Detects return type and formats accordingly
7. **Display** - Shows results as text, JSON, images, or plots

## Requirements

- Python 3.12+
- FastAPI
- Uvicorn
- Pydantic
- Jinja2
- python-multipart

Optional for examples:
- Pillow (for image processing)
- Matplotlib (for plots)
- NumPy (for numerical computations)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Beltrán Offerrall
