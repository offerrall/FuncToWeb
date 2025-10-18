# Func To Web 0.7.2

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
> **Note:** Try entering `b=0` to see how errors are automatically handled and displayed in the UI.

## Installation

```bash
pip install func-to-web
```

## Examples

**Check the `examples/` folder** for 20+ complete, runnable examples covering everything from basic forms to image processing and data visualization. Each example is a single Python file you can run immediately:

```bash
python examples/01_basic_division.py
python examples/08_image_blur.py
python examples/20_lists_limits.py
```

![Examples Preview](images/example_20.jpg)

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

### Lists (New in 0.5.0)

Create dynamic lists of any type with add/remove buttons:

```python
from func_to_web import run
from func_to_web.types import Color, Email
from typing import Annotated
from pydantic import Field

def process_data(
    # Basic type lists
    numbers: list[int],                                         # Default: None
    colors: list[Color],                                        # List of color pickers
    names: list[str] = ["Alice", "Bob"],                        # List with defaults
    
    # Lists with item constraints
    scores: list[Annotated[int, Field(ge=0, le=100)]],          # Each item: 0-100
    usernames: list[Annotated[str, Field(min_length=3)]],       # Each item: min 3 chars
    
    # Lists with list-level constraints
    team: Annotated[list[str], Field(min_length=2, max_length=5)],  # 2-5 items required
    
    # Lists with both item and list constraints
    ratings: Annotated[
        list[Annotated[int, Field(ge=1, le=5)]], 
        Field(min_length=3, max_length=10)
    ],                                                          # 3-10 ratings, each 1-5
    
    # Optional lists
    tags: list[str] | None = None,                              # Can be None or have values
    emails: list[Email] | None = None                           # Optional email list
):
    return f"Processed {len(numbers)} numbers, {len(names)} names"

run(process_data)
```

**Key features:**
- Dynamic add/remove buttons for each list
- Works with all types: `int`, `float`, `str`, `bool`, `date`, `time`, `Color`, `Email`, files
- Not supported with `Literal`
- **Item constraints**: `list[Annotated[int, Field(ge=1, le=100)]]` - validates each item
- **List constraints**: `Annotated[list[int], Field(min_length=2, max_length=10)]` - validates list size
- **Combined constraints**: `Annotated[list[Annotated[int, Field(...)], Field(...)]]`
- Optional lists with toggle: `list[str] | None` or `list[str] | OptionalDisabled`
- Default values: `list[str] = ["hello", "world"]`
- **Default behavior**: Lists without values default to `None` (empty lists `[]` are converted to `None`)
- Individual validation per item with error messages
- List-level validation for size constraints (`min_length`, `max_length`)
- Empty/whitespace values automatically filtered out

![Dynamic Lists](images/lists.jpg)

### Optional Parameters

Use `Type | None` syntax to make parameters optional with a visual toggle switch:

```python
from func_to_web import run
from func_to_web.types import OptionalEnabled, OptionalDisabled, Email
from typing import Annotated
from pydantic import Field

def create_user(
    username: str,  # Required field
    
    # Automatic behavior (standard Python syntax)
    age: int | None = None,  # Disabled (no default value)
    city: str | None = "Madrid",  # Enabled (has default value)
    
    # Explicit control (new in 0.4.4)
    email: Email | OptionalEnabled,  # Always starts enabled
    phone: str | OptionalDisabled,  # Always starts disabled
    bio: Annotated[str, Field(max_length=500)] | OptionalDisabled = "Dev",  # Disabled despite default
):
    result = f"Username: {username}"
    if age:
        result += f", Age: {age}"
    if city:
        result += f", City: {city}"
    if email:
        result += f", Email: {email}"
    if phone:
        result += f", Phone: {phone}"
    if bio:
        result += f", Bio: {bio}"
    return result

run(create_user)
```

![Optional Parameters](images/optional_fields.jpg)

**How it works:**
- Optional fields display a toggle switch to enable/disable them
- **Automatic mode** (`Type | None`): Enabled if has default value, disabled if no default
- **Explicit mode** (`Type | OptionalEnabled/OptionalDisabled`): You control the initial state, overriding defaults
- Disabled fields automatically send `None` to your function
- Works with all field types and constraints (including lists!)

Use automatic mode for standard Python conventions, or explicit mode when you need precise control over which fields start active.

### Special Input Types

```python
from func_to_web import run
from func_to_web.types import Color, Email

def create_account(
    email: Email,
    favorite_color: Color = "#3b82f6",  # Default blue, required
    secondary_color: Color | None = "#10b981",  # Default green, optional
    tertiary_color: Color | None = None,  # No default, optional
):
    """Create account with special input types"""
    return f"Account for {email} with colors {favorite_color}, {secondary_color}, {tertiary_color}"

run(create_account)
```

![Color Picker](images/color.jpg)

### File Uploads

```python
from func_to_web import run
from func_to_web.types import ImageFile, DataFile, TextFile, DocumentFile

def process_files(
    photo: ImageFile,       # .png, .jpg, .jpeg, .gif, .webp
    data: DataFile,         # .csv, .xlsx, .xls, .json
    notes: TextFile,        # .txt, .md, .log
    report: DocumentFile    # .pdf, .doc, .docx
):
    return "Files uploaded!"

run(process_files)
```

You can also use lists of files:

```python
def process_images(
    images: list[ImageFile],  # Upload multiple images
):
    return f"Processed {len(images)} images"
```

![File Upload](images/files.jpg)

### Upload Progress & Performance

When uploading files, you'll see:
- Real-time progress bar (0-100%)
- File size display (e.g., "Uploading 245 MB of 1.2 GB")
- Upload speed and status messages
- Processing indicator when server is working

![Upload Progress](images/upload.jpg)

**Performance highlights:**
- **Optimized streaming**: Files are uploaded in 8MB chunks, reducing memory usage
- **Large file support**: Efficiently handles files from 1GB to 10GB+
- **High speeds**: ~237 MB/s on localhost, ~100-115 MB/s on Gigabit Ethernet
- **Low memory footprint**: Constant memory usage regardless of file size
- **No blocking**: Submit button disabled during upload to prevent duplicates

The progress bar uses `XMLHttpRequest` to track upload progress in real-time, providing instant feedback to users even with very large files.

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
from func_to_web import run
from pydantic import Field

def register(
    age: Annotated[int, Field(ge=18, le=120)],  # Min/max values
    username: Annotated[str, Field(min_length=3, max_length=20)],  # Length limits
    rating: Annotated[float, Field(gt=0, lt=5)]  # Exclusive bounds
):
    return f"User {username}, age {age}, rating {rating}"

run(register)
```

![Validation](images/limits.jpg)

### Return Images & Plots

func-to-web automatically detects and displays images from PIL/Pillow and matplotlib:

```python
from func_to_web import run
from func_to_web.types import ImageFile
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

### File Downloads (New in 0.6.0)

Return files from your functions and users get automatic download buttons:

```python
from func_to_web import run
from func_to_web.types import FileResponse

def create_text_file(content: str):
    data = content.encode('utf-8')
    return FileResponse(data=data, filename="ttutut.txt")

def create_multiple_files(name: str):
    file1 = FileResponse(
        data=f"Hello {name}!".encode('utf-8'),
        filename="hello.txt"
    )
    file2 = FileResponse(
        data=f"Goodbye {name}!".encode('utf-8'),
        filename="goodbye.txt"
    )
    return [file1, file2]

run([create_text_file, create_multiple_files])
```

![File Downloads](images/return_files.jpg)

**Key features:**
- **Single file**: Return `FileResponse(data=bytes, filename="file.ext")`
- **Multiple files**: Return `[FileResponse(...), FileResponse(...)]`
- **Any file type**: PDF, Excel, ZIP, images, JSON, CSV, binary data, etc.
- **Large files**: Uses streaming like uploads - handles GB+ files efficiently
- **Clean UI**: List of files with individual download buttons
- **Automatic cleanup**: Temporary files removed after download

**Works with any library:**
```python
# PDF generation
from reportlab.pdfgen import canvas
import io

def create_pdf(title: str):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 750, title)
    pdf.save()
    return FileResponse(data=buffer.getvalue(), filename="document.pdf")

# Excel generation
import pandas as pd

def create_excel(rows: int):
    df = pd.DataFrame({'A': range(rows), 'B': range(rows)})
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    return FileResponse(data=buffer.getvalue(), filename="data.xlsx")

# ZIP files
import zipfile

def create_archive(file_count: int):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        for i in range(file_count):
            zf.writestr(f'file{i}.txt', f'Content {i}')
    return FileResponse(data=buffer.getvalue(), filename="archive.zip")
```

**Performance:**
- No size limits - uses temporary files and streaming
- Constant memory usage regardless of file size
- Same efficiency as file uploads (8MB chunks)
- Files cleaned up automatically after download

> **Note:** Generated files are stored in the system's temporary directory and automatically deleted after download. Files not downloaded will be cleaned up by the operating system's temporary folder cleanup policies (typically on restart or after several days). For high-traffic production environments with many generated files, consider implementing custom cleanup logic.

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


## Dark Mode (New in 0.7.0)

Toggle between light and dark themes. Your preference is saved automatically.

![Dark Mode](images/dark_mode.jpg)

Click the 🌙/☀️ button in the top-right corner to switch themes. Works on all pages, zero configuration needed.

## Features

### Input Types
- `int`, `float`, `str`, `bool` - Basic types
- `date`, `time` - Date and time pickers
- `Color` - Color picker with preview
- `Email` - Email validation
- `Literal[...]` - Dropdown selections, static or dynamic
- `ImageFile`, `DataFile`, `TextFile`, `DocumentFile` - File uploads
- `list[Type]` - Dynamic lists of any type (new in 0.5.0)
- All types support optional `| None` for toggles

### Validation
- **Numeric**: `ge`, `le`, `gt`, `lt` (min/max bounds)
- **String**: `min_length`, `max_length`, `pattern` (regex)
- **Lists**: Must have at least 1 valid element when enabled, you can also set `min_length` and `max_length` for lists
- **Default values**: Set in function signature

### Output Types
- **Text/Numbers/Dicts** - Formatted as JSON
- **PIL Images** - Displayed as images
- **Matplotlib Figures** - Rendered as PNG
- **Any object** - Converted with `str()`
- **FileResponse** - Single or multiple downloadable files

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

## How It Works

1. **Analysis** - Inspects function signature using `inspect`
2. **Validation** - Validates type hints and constraints using `pydantic`
3. **Form Generation** - Builds HTML form fields from metadata
4. **File Handling** - Streams uploaded files to temp locations in chunks
5. **Server** - Runs FastAPI server with auto-generated routes
6. **Result Processing** - Detects return type and formats accordingly
7. **Display** - Shows results as text, JSON, images, or plots
8. **Progress Tracking** - Real-time feedback during uploads and processing


**454 unit tests** ensuring reliability:

### Test Coverage

- `analyze()`: Function signature analysis, type detection, constraint extraction
- `validate_params()`: Type conversion, constraint validation, optional toggles
- `build_form_fields()`: HTML field generation, format conversion, edge cases

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_analyze.py -v
pytest tests/test_validate.py -v
pytest tests/test_build_form_fields.py -v
```

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

## Performance Notes

### Startup Performance
The first request after server start may take ~300-500ms due to:
- Template compilation
- Module imports
- FastAPI initialization

Subsequent requests are typically <5ms. This is normal Python/FastAPI behavior.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

When contributing, please:
- Add tests for new features
- Ensure all existing tests pass (`pytest tests/ -v`)
- Update documentation as needed

## Author

Beltrán Offerrall