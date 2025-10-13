from func_to_web import run
from typing import Annotated
from pydantic import Field

def rate_movies(
    # Each rating 1-5, need 3-10 ratings total
    ratings: Annotated[
        list[Annotated[int, Field(ge=1, le=5)]],
        Field(min_length=3, max_length=10)
    ]
):
    avg = sum(ratings) / len(ratings)
    return f"Average rating: {avg:.1f} ⭐"

run(rate_movies)