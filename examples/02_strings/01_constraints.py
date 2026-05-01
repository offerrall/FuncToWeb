from typing import Annotated
from pydantic import Field
from func_to_web import run

def register(
    username: Annotated[str, Field(min_length=3, max_length=20)],
    phone:    Annotated[str, Field(pattern=r"^\+?[0-9]{10,15}$")],
):
    return f"User: {username}, Phone: {phone}"

run(register)
