"""An Enum parameter becomes a closed set of options."""

from enum import Enum
from typing import Annotated

from func_to_web import Label, Min, run


class Priority(Enum):
    """How urgent a ticket is."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


DEADLINES = {
    Priority.LOW: 30,
    Priority.NORMAL: 14,
    Priority.HIGH: 3,
    Priority.CRITICAL: 1,
}


def open_ticket(
    title: Annotated[str, Min(3)],
    priority: Annotated[Priority, Label("Priority")] = Priority.NORMAL,
) -> str:
    """Report the deadline that a priority implies."""
    days = DEADLINES[priority]

    return f"{title} [{priority.value}] must be closed within {days} day(s)"


if __name__ == "__main__":
    run(open_ticket, title="Enum type")
