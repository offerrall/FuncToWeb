from typing import Annotated
from pydantic import Field
from func_to_web import run

def grade(
    scores: list[Annotated[int, Field(ge=0, le=100)]],
):
    return f"Average: {sum(scores) / len(scores):.1f}"

run(grade)
