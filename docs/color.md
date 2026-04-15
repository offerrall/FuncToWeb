# Color Input

Use `Color` for hex color inputs. Renders as a native color picker with a hex value display.

`Color` is a ready-made string type — under the hood it's a `str` with a hex pattern validator (`#RGB` or `#RRGGBB`).

## Basic Usage

```python
from func_to_web import run
from func_to_web.types import Color

def basic(background: Color):
    return f"Color: {background}"

run(basic)
```

![Basic Usage](images/color1.jpg)

## Default Value

```python
from func_to_web import run
from func_to_web.types import Color

def defaults(background: Color = "#FF5733"):
    return f"Color: {background}"

run(defaults)
```

![Default Value](images/color2.jpg)

## Label & Description

```python
from typing import Annotated
from func_to_web import run
from func_to_web.types import Color, Label, Description

def label_description(
    background: Annotated[Color, Label("Background Color"), Description("Pick a hex color")],
):
    return f"Color: {background}"

run(label_description)
```

![Label & Description](images/color3.jpg)

## Optional

```python
from func_to_web import run
from func_to_web.types import Color

def optional(background: Color | None = None):
    return f"Color: {background}"

run(optional)
```

> For full control over the toggle's initial state (`OptionalEnabled` / `OptionalDisabled`), see [Optional Types](optional.md).

![Optional](images/color4.jpg)

## List

```python
from func_to_web import run
from func_to_web.types import Color

def list_inputs(palette: list[Color]):
    return f"Palette: {palette}"

run(list_inputs)
```

> For list constraints and more, see [Lists](lists.md).

![List](images/color5.jpg)