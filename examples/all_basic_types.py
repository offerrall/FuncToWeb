from datetime import date, time

from func_to_web import run


def showcase_types(
    name: str,
    age: int,
    height: float,
    active: bool,
    birthday: date,
    alarm: time,
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