from func_to_web import run
from func_to_web.types import Color

def pick(background: Color = "#FF5733"):
    return f"Color: {background}"

run(pick)
