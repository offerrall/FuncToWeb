from typing import Annotated
from func_to_web import run
from func_to_web.types import Dropdown

def get_users():
    return ["alice", "bob", "charlie"]

def assign_task(task: str, user: Annotated[str, Dropdown(get_users)]):
    return f"Assigned '{task}' to {user}"

run(assign_task)
