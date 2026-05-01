from typing import Annotated
from pydantic import Field
from func_to_web import run, Params

class Address(Params):
    street: str
    city:   str
    zip:    Annotated[str, Field(pattern=r"^\d{5}$")]

def register(user_id: int, address: Address, notify: bool = True):
    return f"User {user_id} at {address.city} ({address.zip})"

run(register)
