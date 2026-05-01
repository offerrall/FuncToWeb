from func_to_web import run, ActionTable, HiddenFunction

ROWS = [
    [1, "Alice",   "alice@example.com"],
    [2, "Bob",     "bob@example.com"],
    [3, "Charlie", "charlie@example.com"],
]

def list_users():
    return ActionTable(
        data=ROWS,
        action=edit_user,
        headers=["id", "name", "email"],
    )

def edit_user(id: int, name: str, email: str):
    return f"Edited #{id}: {name} <{email}>"

run([list_users, HiddenFunction(edit_user)])
