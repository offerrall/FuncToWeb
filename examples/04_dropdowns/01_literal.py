from typing import Literal
from func_to_web import run

def export(
    format:   Literal["json", "csv", "xml"],
    priority: Literal[1, 2, 3] = 2,
):
    return f"Exporting as {format}, priority {priority}"

run(export)
