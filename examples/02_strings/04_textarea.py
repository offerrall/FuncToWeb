from typing import Annotated
from func_to_web import run
from func_to_web.types import Rows

def feedback(message: Annotated[str, Rows(8)]):
    return f"Got {len(message)} chars"

run(feedback)
