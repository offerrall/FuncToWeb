from typing import Annotated
from pydantic import Field
from func_to_web import run
from func_to_web.types import Slider

def silent(
    silent_volume: Annotated[int, Field(ge=0, le=100), Slider(show_value=False)] = 0,
):
    return f"Volume: {silent_volume}"

run(silent)
