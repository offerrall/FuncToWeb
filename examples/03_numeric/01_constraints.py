from typing import Annotated
from pydantic import Field
from func_to_web import run

def profile(
    age:   Annotated[int,   Field(ge=18, le=120)],
    ratio: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5,
):
    return f"Age: {age}, Ratio: {ratio}"

run(profile)
