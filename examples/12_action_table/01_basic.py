from func_to_web import run, ActionTable, HiddenFunction

USERS = [
    {"id": 1, "name": "Alice",   "role": "admin"},
    {"id": 2, "name": "Bob",     "role": "user"},
    {"id": 3, "name": "Charlie", "role": "user"},
]

def list_users():
    return ActionTable(data=USERS, action=edit_user)

def edit_user(id: int, name: str, role: str):
    return f"Edited user {id}: {name} ({role})"

run([list_users, HiddenFunction(edit_user)])
