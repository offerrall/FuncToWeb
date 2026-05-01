from typing import Annotated
from pydantic import Field
from func_to_web import run
from func_to_web.types import PatternMessage

def add_phone(
    phone: Annotated[
        str,
        Field(pattern=r"^\+?[0-9]{10,15}$"),
        PatternMessage("Enter a valid phone (e.g. +34612345678)"),
    ],
):
    return f"Phone saved: {phone}"

run(add_phone)
