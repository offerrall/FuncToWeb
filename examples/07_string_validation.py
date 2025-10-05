from FuncToWeb import run, Email
from typing import Annotated
from pydantic import Field

def register_user(
    username: Annotated[str, Field(min_length=3, max_length=20)],
    email: Email,
    password: Annotated[str, Field(min_length=8, max_length=50)],
    bio: Annotated[str, Field(max_length=200)] = ""
):
    """User registration with validation"""
    return {
        "username": username,
        "email": email,
        "password_length": len(password),
        "bio": bio or "No bio provided"
    }

run(register_user)