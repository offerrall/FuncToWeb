import json
from pathlib import Path
from typing import Annotated
from pydantic import Field
from func_to_web import run, ActionTable, HiddenFunction, Params, Email

DB_FILE = Path("users.json")


class UserData(Params):
    name: Annotated[str, Field(min_length=2, max_length=50)]
    email: Email
    phone: Annotated[str, Field(pattern=r'^\+?[0-9]{9,15}$')]


def _load() -> dict:
    if not DB_FILE.exists():
        return {}
    return {int(k): v for k, v in json.loads(DB_FILE.read_text()).items()}


def _save(db: dict):
    DB_FILE.write_text(json.dumps(db, indent=2))


def _check(db: dict, id: int):
    if id not in db:
        raise ValueError(f"User {id} not found")


def _user_dict(uid: int, data: UserData) -> dict:
    return {"id": uid, **vars(data)}


def edit_users():
    """Edit users"""
    return ActionTable(data=_load, action=edit_user)


def delete_users():
    """Delete users"""
    return ActionTable(data=_load, action=delete_user)


def create_user(data: UserData):
    """Create a new user"""
    db = _load()
    uid = max(db) + 1 if db else 1
    db[uid] = _user_dict(uid, data)
    _save(db)
    return f"User {uid} created"


def edit_user(id: int, data: UserData):
    """Edit an existing user"""
    db = _load()
    _check(db, id)
    db[id] = _user_dict(id, data)
    _save(db)
    return f"User {id} updated"


def delete_user(id: int):
    """Delete a user"""
    db = _load()
    _check(db, id)
    del db[id]
    _save(db)
    return f"User {id} deleted"


run([edit_users, delete_users, create_user, HiddenFunction(delete_user), HiddenFunction(edit_user)])