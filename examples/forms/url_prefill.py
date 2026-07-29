"""prefill and hidden are query parameters: any URL opens a filled form."""

import json
from datetime import date
from typing import Annotated
from urllib.parse import urlencode

from func_to_web import Max, Min, WebFunction, run

HOST = "127.0.0.1"
PORT = 8000
SLUG = "edit-task"

TASKS = {
    1: {"title": "Write the release notes", "due": "2026-08-03",
        "done": False},
    2: {"title": "Review the pull request", "due": "2026-08-05",
        "done": True},
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


def edit_url(task_id: int) -> str:
    """Build the URL that opens the form filled with one stored task.

    Values travel in the browser transport format, so due is an ISO date
    string, and task_id is hidden because it identifies the record.
    """
    prefill = {"task_id": task_id, **TASKS[task_id]}
    query = urlencode(
        {
            "prefill": json.dumps(prefill),
            "hidden": json.dumps(["task_id"]),
        }
    )

    return f"http://{HOST}:{PORT}/{SLUG}/?{query}"


if __name__ == "__main__":
    print(f"Create: http://{HOST}:{PORT}/{SLUG}/")

    for identifier in TASKS:
        print(f"Edit {identifier}: {edit_url(identifier)}")

    run(
        WebFunction(edit_task, slug=SLUG),
        title="Tasks",
        host=HOST,
        port=PORT,
    )
