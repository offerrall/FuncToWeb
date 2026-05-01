import os
from func_to_web import run

def restricted(action: str):
    return f"Done: {action}"

run(
    restricted,
    auth={"admin": os.environ.get("ADMIN_PASSWORD", "dev")},
    secret_key=os.environ.get("SECRET_KEY"),
)
