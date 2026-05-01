import time
from func_to_web import run, ActionTable, HiddenFunction

def fetch_users():
    """Simulates a fresh DB query — runs every render."""
    return [
        {"id": 1, "name": "Alice",   "last_seen": time.strftime("%H:%M:%S")},
        {"id": 2, "name": "Bob",     "last_seen": time.strftime("%H:%M:%S")},
    ]

def list_users():
    return ActionTable(data=fetch_users, action=ping_user)

def ping_user(id: int, name: str):
    return f"Pinged user {id} ({name})"

run([list_users, HiddenFunction(ping_user)])
