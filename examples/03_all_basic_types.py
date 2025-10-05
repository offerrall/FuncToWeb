from FuncToWeb import run
from datetime import date, time

def showcase_types(
    name: str = "John",
    age: int = 25,
    height: float = 1.75,
    active: bool = True,
    birthday: date = date(2000, 1, 1),
    alarm: time = time(7, 30)
):
    """Demonstrates all basic types"""
    return {
        "name": name,
        "age": age,
        "height": height,
        "active": active,
        "birthday": str(birthday),
        "alarm": str(alarm)
    }

run(showcase_types)