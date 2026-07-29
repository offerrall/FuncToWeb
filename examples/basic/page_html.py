"""page_of() is the HTML of one opening, rendered without serving anything."""

from datetime import date
from pathlib import Path
from tempfile import mkdtemp
from typing import Annotated

from func_to_web import Max, Min, WebFunction, page_of

TASK = {
    "task_id": 7,
    "title": "Write the release notes",
    "due": date(2026, 8, 3),
    "done": False,
}


def edit_task(
    task_id: Annotated[int, Min(1)],
    title: Annotated[str, Min(3), Max(80)],
    due: date,
    done: bool = False,
) -> str:
    """Save the edited task."""
    state = "done" if done else "pending"

    return f"Task {task_id}: {title} ({state}, due {due.isoformat()})"


def opening_html() -> str:
    """Render the edit form of one task, with its identifier out of sight.

    prefill proposes the initial values as real Python objects —a date is a
    date here, not the ISO string the browser transports— and hidden names
    the parameters this opening does not show. Neither touches the
    WebFunction, which compiled its own page once and can be rendered again
    with other values as many times as needed. What comes back is markup and
    only markup: no route is mounted and no server is started, and the page
    asks a space for its /static assets, so it is meant to be served from
    inside one.
    """
    return page_of(
        WebFunction(edit_task),
        prefill=TASK,
        hidden=("task_id",),
    )


if __name__ == "__main__":
    path = Path(mkdtemp()) / "edit-task.html"
    path.write_text(opening_html(), encoding="utf-8")

    print(f"{path} ({path.stat().st_size} bytes)")
