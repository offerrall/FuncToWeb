from typing import Annotated
from pydantic import Field
from func_to_web import run
from func_to_web.types import Slider, Label, Description, IsPassword

PositiveInt   = Annotated[int, Field(ge=0)]
BoundedInt    = Annotated[PositiveInt, Field(le=100)]
SliderInt     = Annotated[BoundedInt, Slider()]
LabeledSlider = Annotated[SliderInt, Label("Level"), Description("0 to 100")]

PasswordStr = Annotated[
    str,
    Field(min_length=8, max_length=50),
    IsPassword(),
    Label("Secure Password"),
]

def configure(level: LabeledSlider, password: PasswordStr):
    return f"Level: {level}, password set: {bool(password)}"

run(configure)
