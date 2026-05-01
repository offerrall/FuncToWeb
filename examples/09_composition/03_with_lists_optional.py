from typing import Annotated
from pydantic import Field
from func_to_web import run
from func_to_web.types import Label

Score = Annotated[int, Field(ge=0, le=100), Label("Score")]

def process(
    scores: list[Score],
    bonus:  Score | None = None,
):
    total = sum(scores) + (bonus or 0)
    return f"Total: {total}"

run(process)
