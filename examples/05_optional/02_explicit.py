from func_to_web import run
from func_to_web.types import OptionalEnabled, OptionalDisabled

def explicit(
    name: str | OptionalEnabled,
    bio:  str | OptionalDisabled = "Developer",
):
    return f"Name: {name}, Bio: {bio}"

run(explicit)
