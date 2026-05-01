from enum import Enum
from func_to_web import run

class Role(Enum):
    ADMIN  = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class Priority(Enum):
    LOW    = 1
    MEDIUM = 2
    HIGH   = 3

def assign(role: Role, priority: Priority):
    return f"Role: {role.name} ({role.value}), Priority: {priority.name}"

run(assign)
