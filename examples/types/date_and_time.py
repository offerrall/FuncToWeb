"""Date and time parameters, which travel as ISO text."""

from datetime import date, datetime, time
from typing import Annotated

from func_to_web import Label, run


def schedule_slot(
    day: Annotated[date, Label("Day of the meeting")],
    starts_at: Annotated[time, Label("Start")],
    ends_at: Annotated[time, Label("End")],
) -> str:
    """Describe a meeting slot and its duration in minutes."""
    if ends_at <= starts_at:
        raise ValueError("the end must be later than the start")

    begin = datetime.combine(day, starts_at)
    finish = datetime.combine(day, ends_at)
    minutes = int((finish - begin).total_seconds() // 60)

    return f"{day.isoformat()} from {starts_at} to {ends_at} ({minutes} min)"


if __name__ == "__main__":
    run(schedule_slot, title="Date and time")
