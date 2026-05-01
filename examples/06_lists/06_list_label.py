from typing import Annotated
from pydantic import Field
from func_to_web import run
from func_to_web.types import Label, Description

def scored(
    scores: Annotated[
        list[Annotated[int, Field(ge=0, le=100), Label("Item Score")]],
        Field(min_length=1, max_length=5),
        Label("Score List"),
        Description("Add between 1 and 5 scores"),
    ],
):
    return f"Scores: {scores}"

run(scored)
