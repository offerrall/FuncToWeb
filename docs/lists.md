# Lists

<div class="grid" markdown>

<div markdown>

## Basic Usage
Create dynamic lists of any type with add/remove buttons.
```python
from func_to_web import run
from func_to_web.types import Color, Email

def process_data(
    # Basic type lists
    numbers: list[int],                      # List of integers
    colors: list[Color],                     # List of color pickers
    names: list[str] = ["Alice", "Bob"],     # List with defaults
):
    return f"Processed {len(numbers)} numbers, {len(names)} names"

run(process_data)
```
## List Constraints
```python
from func_to_web import run
from typing import Annotated
from pydantic import Field

def rate_movies(
    # Each rating 1-5, need 3-10 ratings total
    ratings: Annotated[
        list[Annotated[int, Field(ge=1, le=5)]],
        Field(min_length=3, max_length=10)
    ]
):
    avg = sum(ratings) / len(ratings)
    return f"Average rating: {avg:.1f} ⭐"

run(rate_movies)
```

## Key Features
- **Dynamic add/remove buttons** for each list
- Works with **all types**: `int`, `float`, `str`, `bool`, `date`, `time`, `Color`, `Email`, Files Types
- Default values: `list[str] = ["hello", "world"]`
- All non-optional lists require at least 1 item
- Not supported with `Literal`
- Lists cannot be nested (e.g., `list[list[int]]` is not supported)

</div>

<div markdown>

![Dynamic Lists](images/lists_basic.jpg)

</div>

</div>


## Next Steps

- [Optional Types](optional.md) - Make parameters optional
- [Dropdowns](dropdowns.md) - Use dropdown menus for inputs