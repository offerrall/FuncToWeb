"""Choices is a closed set: a dropdown that is also a real constraint."""

from typing import Annotated

from func_to_web import Choices, Label, run


def book_room(
    room: Annotated[
        str,
        Choices(values=("Focus", "Studio", "Boardroom")),
        Label("Meeting room"),
    ],
    hours: Annotated[int, Choices(values=(1, 2, 4, 8)), Label("Duration")] = 2,
) -> str:
    """Book a meeting room from two closed sets of options.

    Choices turns the field into a dropdown and is still a real constraint:
    a value outside the tuple is rejected whatever the client sends.
    """
    return f"{room} booked for {hours}h"


if __name__ == "__main__":
    run(book_room, title="Closed sets of options")
