from typing import Annotated
from pydantic import Field
from func_to_web import run
from func_to_web.types import Slider, Label

Volume = Annotated[int,   Field(ge=0, le=100), Slider(), Label("Volume")]
Speed  = Annotated[float, Field(ge=0.1, le=4.0), Label("Speed")]

def play(volume: Volume = 80, speed: Speed = 1.0):
    return f"Playing at vol={volume}, speed={speed}x"

def record(volume: Volume = 50):
    return f"Recording at vol={volume}"

run([play, record])
