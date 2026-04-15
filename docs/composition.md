# Type Composition

`Annotated` lets you layer constraints, UI metadata, and widgets into reusable types. Define your vocabulary once and reuse it across every function.

## Basic Composition

```python
from typing import Annotated
from pydantic import Field
from func_to_web import run
from func_to_web.types import Slider, Step, Label, Description, Placeholder, IsPassword, Rows

# Constrained base types
PositiveInt  = Annotated[int,   Field(ge=0)]
BoundedInt   = Annotated[int,   Field(ge=0, le=100)]
SmallStr     = Annotated[str,   Field(min_length=1, max_length=50)]
LongStr      = Annotated[str,   Field(min_length=1, max_length=5000)]
UnitFloat    = Annotated[float, Field(ge=0.0, le=1.0)]

# Add widgets on top
SliderInt    = Annotated[BoundedInt, Slider()]
SliderStep5  = Annotated[BoundedInt, Slider(), Step(5)]
PasswordStr  = Annotated[SmallStr,   IsPassword()]
TextAreaStr  = Annotated[LongStr,    Rows(10)]
StepFloat    = Annotated[UnitFloat,  Step(0.01)]

# Add labels and descriptions on top of everything
LabeledSlider = Annotated[SliderInt,   Label("Volume")]
FullSlider    = Annotated[SliderStep5, Label("Level"),    Description("Set the level")]
FullPassword  = Annotated[PasswordStr, Label("Password"), Placeholder("********")]
FullTextArea  = Annotated[TextAreaStr, Label("Notes"),    Placeholder("Write here...")]
```

Use them directly as type hints:

```python
def configure(
    volume:   LabeledSlider = 50,
    opacity:  StepFloat     = 1.0,
    password: FullPassword,
    notes:    FullTextArea  = "",
):
    return f"Volume: {volume}, Opacity: {opacity}"

run(configure)
```

## Constraint Merging

Constraints merge across layers. If the same constraint appears in multiple layers, **the last one wins**:

```python
from typing import Annotated
from pydantic import Field

PositiveInt = Annotated[int, Field(ge=0)]

# ge=0 from PositiveInt + le=100 added → both apply
BoundedInt = Annotated[PositiveInt, Field(le=100)]

# ge=0 from PositiveInt, then ge=10 overrides → final ge=10
StrictInt = Annotated[PositiveInt, Field(ge=10)]

# Three levels deep → final ge=10
L1 = Annotated[int,  Field(ge=0)]
L2 = Annotated[L1,   Field(ge=5)]
L3 = Annotated[L2,   Field(ge=10)]  # ge=10 wins
```

## Reusing Across Functions

The real power is sharing types across multiple functions without repeating yourself:

```python
from typing import Annotated
from pydantic import Field
from func_to_web import run
from func_to_web.types import Slider, Label, Description

Volume  = Annotated[int,   Field(ge=0, le=100), Slider(), Label("Volume")]
Quality = Annotated[int,   Field(ge=1, le=10),  Slider(), Label("Quality")]
Speed   = Annotated[float, Field(ge=0.1, le=4.0), Label("Speed")]

def export_video(volume: Volume = 80, quality: Quality = 7, speed: Speed = 1.0):
    return f"Exporting: vol={volume}, q={quality}, speed={speed}"

def preview_video(volume: Volume = 50, speed: Speed = 1.0):
    return f"Previewing: vol={volume}, speed={speed}"

run([export_video, preview_video])
```

Change `Volume` once and it updates everywhere.

## Combining with Lists and Optional

Composed types work seamlessly with `list` and `| None`:

```python
from typing import Annotated
from pydantic import Field
from func_to_web import run
from func_to_web.types import Label

Score = Annotated[int, Field(ge=0, le=100), Label("Score")]

def process(
    scores:       list[Score],         # List of bounded ints
    bonus:        Score | None = None, # Optional bounded int
):
    return f"Scores: {scores}, Bonus: {bonus}"

run(process)
```