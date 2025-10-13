from func_to_web import run
from func_to_web.types import Color, Email, OptionalEnabled
from typing import Annotated
from pydantic import Field

def process_data(
    # Basic type lists
    numbers: list[int],                                         # Default: None
    colors: list[Color],                                        # List of color pickers
    
    # Lists with item constraints
    scores: list[Annotated[int, Field(ge=0, le=100)]],          # Each item: 0-100
    usernames: list[Annotated[str, Field(min_length=3)]],       # Each item: min 3 chars
    
    # Lists with list-level constraints
    team: Annotated[list[str], Field(min_length=2, max_length=5)],  # 2-5 items required
    
    # Lists with both item and list constraints
    ratings: Annotated[
        list[Annotated[int, Field(ge=1, le=5)]], 
        Field(min_length=3, max_length=10)
    ],                                                          # 3-10 ratings, each 1-5
    names: list[str] = ["Alice", "Bob"],                        # List with defaults
    # Optional lists
    tags: list[str] | None = None,                              # Can be None or have values
    emails: list[Email] | None = None,                          # Optional email list

    # Optional more min-max examples
    all_features: Annotated[
        list[Annotated[str, Field(min_length=2)]],
        Field(min_length=2)
    ] | OptionalEnabled = ["aaa", "bbb"]                         # 1-4 items, each min 2 chars
):
    data = {
        "numbers": numbers,
        "colors": colors,
        "scores": scores,
        "usernames": usernames,
        "team": team,
        "ratings": ratings,
        "names": names,
        "tags": tags,
        "emails": emails,
        "all_features": all_features
    }
    return data

run(process_data)