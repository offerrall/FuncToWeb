from typing import Annotated
from func_to_web import run
from func_to_web.types import IsPassword

def login(user: str, password: Annotated[str, IsPassword()]):
    return f"Logged in as {user}"

run(login)
