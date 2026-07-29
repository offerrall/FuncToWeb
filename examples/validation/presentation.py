"""Label, Description and Placeholder change the page, never the contract."""

from typing import Annotated

from func_to_web import Description, Label, Max, Min, Placeholder, run


def open_ticket(
    title: Annotated[
        str,
        Label("Ticket title"),
        Description("One line naming what is broken."),
        Placeholder("Login fails after a password reset"),
        Min(5),
        Max(80),
    ],
    priority: Annotated[
        int,
        Label("Priority"),
        Description("1 is urgent, 5 can wait."),
        Min(1),
        Max(5),
    ] = 3,
) -> str:
    """Open a support ticket with a form that explains itself.

    Label renames the field, Description adds the help text under it and
    Placeholder is the greyed-out hint inside the empty box. None of the three
    changes what the function accepts.
    """
    return f"[P{priority}] {title}"


if __name__ == "__main__":
    run(open_ticket, title="Field presentation")
