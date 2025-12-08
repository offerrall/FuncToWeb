from enum import Enum
from func_to_web import run

class Theme(Enum):
    LIGHT = 'light'
    DARK = 'dark'
    AUTO = 'auto'

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

def create_task(
    theme: Theme,
    priority: Priority
):
    """Your function receives the Enum member"""
    # Access both name and value
    return f"Theme: {theme.name} ({theme.value}), Priority: {priority.value}"

run(create_task)