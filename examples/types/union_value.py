"""Unions: one parameter, several possible shapes."""

from datetime import date
from typing import Annotated

from func_to_web import Label, Max, Min, run


def register_reading(
    sensor: Annotated[str, Min(1), Max(20)] | Annotated[int, Min(1), Max(999)],
    value: Annotated[int, Min(-100), Max(100)]
    | Annotated[float, Min(-100.0), Max(100.0)],
    taken_on: Annotated[date, Label("Taken on")] | None = None,
) -> str:
    """Accept a sensor named by text or number and an int or float reading."""
    identifier = (
        f"sensor #{sensor}" if type(sensor) is int else f"sensor {sensor!r}"
    )
    kind = type(value).__name__
    when = "today" if taken_on is None else taken_on.isoformat()

    return f"{identifier} reported {value} ({kind}) on {when}"


if __name__ == "__main__":
    run(register_reading, title="Union value")
