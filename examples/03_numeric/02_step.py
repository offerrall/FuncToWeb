from typing import Annotated
from func_to_web import run
from func_to_web.types import Step

def tune(
    count: Annotated[int,   Step(5)]   = 0,
    ratio: Annotated[float, Step(0.1)] = 0.0,
):
    return f"Count: {count}, Ratio: {ratio}"

run(tune)
