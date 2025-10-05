# FuncToWeb

**Transform any Python function into a web interface automatically.**

FuncToWeb is a minimalist library that generates web UIs from your Python functions with zero boilerplate. Just add type hints, call `run()`, and you're done.

**The entire library is just 250 lines of Python and 600 lines of HTML/CSS/JS.** Simple, powerful, and easy to understand.

## Installation

```bash
pip install functoweb
```

## Quick Start

```python
from FuncToWeb import run

def dividir(a: int, b: int):
    return a / b

run(dividir)
```

Open `http://127.0.0.1:8000` in your browser to see the generated form.

## What Can You Do?

FuncToWeb automatically generates beautiful web forms for any Python function. Here's everything it supports:

### Basic Types
```python
from FuncToWeb import run
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

### Special Input Types
```python
from FuncToWeb import run, Color, Email

def special_inputs(
    favorite_color: Color,  # Color picker
    contact: Email          # Email validation
):
    return f"Color: {favorite_color}, Email: {contact}"

run(special_inputs)
```

### File Uploads
```python
from FuncToWeb import run, ImageFile, DataFile, TextFile, DocumentFile, AnyFile

def process_files(
    photo: ImageFile,       # .png, .jpg, .jpeg, .gif, .webp
    data: DataFile,         # .csv, .xlsx, .xls, .json
    notes: TextFile,        # .txt, .md, .log
    report: DocumentFile,   # .pdf, .doc, .docx
    anything: AnyFile       # Any file type
):
    return "Files uploaded!"

run(process_files)
```

### Dropdowns
```python
from typing import Literal
from FuncToWeb import run

def preferences(
    theme: Literal['light', 'dark', 'auto'],
    language: Literal['en', 'es', 'fr']
):
    return f"Theme: {theme}, Language: {language}"

run(preferences)
```

### Constraints & Validation
```python
from typing import Annotated
from pydantic import Field
from FuncToWeb import run

def register(
    age: Annotated[int, Field(ge=18, le=120)],              # Min/max values
    username: Annotated[str, Field(min_length=3, max_length=20)],  # Length limits
    rating: Annotated[float, Field(gt=0, lt=5)]             # Exclusive bounds
):
    return f"User {username}, age {age}, rating {rating}"

run(register)
```

### Default Values
```python
from FuncToWeb import run

def greet(name: str = "World", count: int = 1):
    return f"Hello {name}! " * count

run(greet)
```

### Return Images & Plots

FuncToWeb automatically detects and displays images from PIL/Pillow and matplotlib:

```python
from FuncToWeb import run, ImageFile
from PIL import Image, ImageFilter

def blur_image(image: ImageFile, radius: int = 5):
    img = Image.open(image)
    return img.filter(ImageFilter.GaussianBlur(radius))

run(blur_image)
```

```python
from FuncToWeb import run
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

## Complete Example

```python
from typing import Annotated, Literal
from pydantic import Field
from datetime import date, time
from FuncToWeb import run, Color, Email, ImageFile

def create_profile(
    # Text with constraints
    name: Annotated[str, Field(min_length=3, max_length=50)] = "John Doe",
    
    # Special types
    email: Email = "user@example.com",
    favorite_color: Color = "#10b981",
    
    # File upload
    avatar: ImageFile = None,
    
    # Date and time
    birth_date: date = date(1990, 1, 1),
    alarm: time = time(7, 30),
    
    # Numeric with constraints
    age: Annotated[int, Field(ge=18, le=120)] = 25,
    
    # Dropdown
    theme: Literal['light', 'dark', 'auto'] = 'auto',
    
    # Checkbox
    newsletter: bool = True
):
    return {
        "name": name,
        "email": email,
        "color": favorite_color,
        "avatar": avatar,
        "birth_date": birth_date.isoformat(),
        "alarm": alarm.isoformat(),
        "age": age,
        "theme": theme,
        "newsletter": newsletter
    }

run(create_profile)
```

## More Examples

Check the `examples/` folder for complete working examples:

- **Basic types** - All supported input types
- **File uploads** - Image processing, CSV analysis
- **Data visualization** - Matplotlib plots and charts
- **Image manipulation** - Filters, transformations with PIL
- **Validation** - Field constraints and custom validation
- **Real-world apps** - Complete mini-applications

Each example is a standalone Python file you can run directly.

## Available Constraints

### Numbers (`int`, `float`)
- `ge` - Greater than or equal (≥)
- `le` - Less than or equal (≤)
- `gt` - Greater than (>)
- `lt` - Less than (<)

### Strings (`str`)
- `min_length` - Minimum length
- `max_length` - Maximum length
- `pattern` - Regex pattern

### File Types
- `ImageFile` - Images (.png, .jpg, .jpeg, .gif, .webp)
- `DataFile` - Data files (.csv, .xlsx, .xls, .json)
- `TextFile` - Text files (.txt, .md, .log)
- `DocumentFile` - Documents (.pdf, .doc, .docx)
- `AnyFile` - Any file with extension

## Return Types

FuncToWeb automatically handles different return types:

- **Text/Numbers/Dicts** - Displayed as formatted JSON
- **PIL Images** - Rendered as images in the browser
- **Matplotlib Figures** - Converted to PNG and displayed
- **Any other object** - Converted to string with `str()`

## Configuration

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

## How It Works

1. **Analysis** - Inspects function signature using `inspect`
2. **Validation** - Validates type hints and constraints using `pydantic`
3. **Form Generation** - Builds HTML form fields from metadata
4. **File Handling** - Saves uploaded files to temp locations
5. **Server** - Runs FastAPI server with auto-generated routes
6. **Result Processing** - Detects return type and formats accordingly
7. **Validation** - Validates data client-side (HTML5) and server-side (Pydantic)

## Why FuncToWeb?

- **Minimalist** - Only 250 lines of Python + 600 lines of HTML/CSS/JS
- **Zero boilerplate** - Just type hints and you're done
- **Powerful** - Supports all common input types including files
- **Smart output** - Automatically displays images, plots, and data
- **Beautiful UI** - Modern, responsive interface out of the box
- **Type-safe** - Full Pydantic validation

## License

MIT

## Author

Created with ❤️ for developers who want instant UIs for their Python functions.