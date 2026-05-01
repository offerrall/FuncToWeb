from typing import Annotated
from pydantic import Field
from func_to_web import run

def team(
    members: Annotated[list[str], Field(min_length=2, max_length=5)],
):
    return f"Team of {len(members)}: {members}"

run(team)
