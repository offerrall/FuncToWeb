from typing import Annotated
from pydantic import Field
from func_to_web import run
from func_to_web.types import Slider

def settings(
    volume:  Annotated[int,   Field(ge=0, le=100), Slider()] = 50,
    opacity: Annotated[float, Field(ge=0.0, le=1.0), Slider()] = 1.0,
):
    return f"Volume: {volume}, Opacity: {opacity}"

run(settings)
