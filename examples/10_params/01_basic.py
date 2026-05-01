from typing import Annotated
from pydantic import Field
from func_to_web import run, Params
from func_to_web.types import Email

class UserData(Params):
    name:  Annotated[str, Field(min_length=2, max_length=50)]
    email: Email
    age:   int = 18

def create(data: UserData):
    return f"Created: {data.name} ({data.age}) <{data.email}>"

run(create)
