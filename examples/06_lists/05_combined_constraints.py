from typing import Annotated
from pydantic import Field
from func_to_web import run

def ratings(
    values: Annotated[
        list[Annotated[int, Field(ge=1, le=5)]],
        Field(min_length=3, max_length=10),
    ],
):
    return f"Avg: {sum(values) / len(values):.2f}"

run(ratings)
