"""Todo — a mini-app where one model feeds three functions, opened as modals.

The dataclass is written once and create_task(), edit_task() and delete_task()
only reference it: the forms, the validation and /doc are read from it, so a new
field reaches all three surfaces without any of them being edited.

The host page is plain HTML of its own. It never builds a form: it opens each
function in a modal and waits on the handle's closed promise, which resolves
with what happened inside, so the list refreshes only after a run that really
completed.

Run:  python todo.py
Open: http://127.0.0.1:8000/ (or /tools/doc, /api/tasks)
"""

from dataclasses import asdict, dataclass
from itertools import count
from typing import Annotated, Literal

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from func_to_web import Label, Max, Min, app_of


@dataclass
class Task:
    title: Annotated[str, Min(1), Max(80), Label("Title")]
    priority: Literal["low", "normal", "high"] = "normal"
    done: bool = False


TASKS: dict[int, Task] = {}
_ids = count(1)


def create_task(task: Task) -> str:
    """Create a task."""
    task_id = next(_ids)
    TASKS[task_id] = task
    return f"Task {task_id} created"


def edit_task(task_id: int, task: Task) -> str:
    """Edit a task."""
    if task_id not in TASKS:
        raise KeyError(f"no task {task_id}")
    TASKS[task_id] = task
    return "Task updated"


def delete_task(task_id: int) -> str:
    """Delete a task."""
    if TASKS.pop(task_id, None) is None:
        raise KeyError(f"no task {task_id}")
    return "Task deleted"


PAGE = """<!doctype html>
<meta charset="utf-8">
<title>Tasks</title>
<style>
body { font: 16px system-ui; max-width: 40rem; margin: 3rem auto; }
li { display: flex; gap: .5rem; align-items: center; margin: .4rem 0; }
li span { flex: 1; }
.done { text-decoration: line-through; opacity: .55; }
</style>

<h1>Tasks</h1>
<p>Every button below opens a Python function. No form is written here.</p>

<button id="new" type="button">New task</button>
<ul id="tasks"></ul>

<script type="module">
import { openModal } from "/tools/static/sdk.js";

const list = document.getElementById("tasks");

async function tasks() {
    const response = await fetch("/api/tasks");

    return response.json();
}

async function run(url, prefill, hidden) {
    const modal = openModal(url, { prefill, hidden, closeOnResult: true });
    const { completed } = await modal.closed;

    if (completed) await refresh();
}

function row(task) {
    const item = document.createElement("li");
    const label = document.createElement("span");

    label.textContent = `#${task.task_id} ${task.title} (${task.priority})`;
    if (task.done) label.className = "done";

    const edit = document.createElement("button");
    edit.type = "button";
    edit.textContent = "Edit";
    edit.addEventListener("click", () => run(
        "/tools/edit_task",
        { task_id: task.task_id, task: { title: task.title,
                                         priority: task.priority,
                                         done: task.done } },
        ["task_id"],
    ));

    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Delete";
    remove.addEventListener("click", () => run(
        "/tools/delete_task", { task_id: task.task_id }, ["task_id"]));

    item.append(label, edit, remove);

    return item;
}

async function refresh() {
    list.replaceChildren(...(await tasks()).map(row));
}

document.getElementById("new").addEventListener(
    "click", () => run("/tools/create_task"));

await refresh();
</script>
"""

app = FastAPI()
app.mount("/tools", app_of([create_task, edit_task, delete_task]))


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """Serve the host page that opens each function in a modal."""
    return PAGE


@app.get("/api/tasks")
def list_tasks() -> list[dict]:
    return [{"task_id": i, **asdict(t)} for i, t in sorted(TASKS.items())]


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
