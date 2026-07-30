"""Todo, stored — the same mini-app, except the tasks survive the restart.

`todo.py` keeps its tasks in a dict that dies with the process. Here the dict
and its id counter are one `store_of(...)` line, and the same `Task` dataclass
that draws the forms is what the file on disk holds. One model, three functions,
and now a JSON file you can open in an editor. The ids outlive the process too,
and `close()` runs on a normal exit, so Ctrl+C is enough.

The file is named after the class and the fingerprint of its schema —
`data/Task.<hash>.json` — so adding a field to `Task` starts a new file and
leaves the old one beside it, whole and readable. Nothing migrates behind your
back.

Needs `pip install pytypehintstore` on top of the library, and writes to
`data/` next to this file so you can look at what it wrote.

Run:  python todo_stored.py
Open: http://127.0.0.1:8000/ (or /tools/doc, /api/tasks)
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Annotated, Literal

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pytypehintstore import store_of

from func_to_web import Label, Max, Min, router_of


@dataclass
class Task:
    title: Annotated[str, Min(1), Max(80), Label("Title")]
    priority: Literal["low", "normal", "high"] = "normal"
    done: bool = False


TASKS = store_of(Task, Path(__file__).parent / "data")


def create_task(task: Task) -> str:
    """Create a task."""
    return f"Task {TASKS.add(task)} created"


def edit_task(task_id: int, task: Task) -> str:
    """Edit a task."""
    if task_id not in TASKS:
        raise KeyError(f"no task {task_id}")
    TASKS.put(task_id, task)
    return "Task updated"


def delete_task(task_id: int) -> str:
    """Delete a task."""
    if task_id not in TASKS:
        raise KeyError(f"no task {task_id}")
    TASKS.remove(task_id)
    return "Task deleted"


PAGE = """<!doctype html>
<meta charset="utf-8">
<title>Tasks</title>
<style>
body { font: 16px system-ui; max-width: 40rem; margin: 3rem auto; }
li { display: flex; gap: .5rem; align-items: center; margin: .4rem 0; }
li span { flex: 1; }
.done { text-decoration: line-through; opacity: .55; }
footer { margin-top: 2rem; font-size: .85rem; opacity: .7; }
code { font-size: .85rem; }
</style>

<h1>Tasks</h1>
<p>Every button below opens a Python function. No form is written here, and
   the list survives a restart.</p>

<button id="new" type="button">New task</button>
<ul id="tasks"></ul>
<footer>Stored in <code id="file"></code> — open it, it is yours.</footer>

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

document.getElementById("file").textContent =
    await (await fetch("/api/file")).json();

await refresh();
</script>
"""

app = FastAPI()
app.include_router(router_of([create_task, edit_task, delete_task]), prefix="/tools")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """Serve the host page that opens each function in a modal."""
    return PAGE


@app.get("/api/tasks")
def list_tasks() -> list[dict]:
    return [{"task_id": i, **asdict(t)} for i, t in TASKS.all()]


@app.get("/api/file")
def file_path() -> str:
    """Where the rows live: the class name and the fingerprint of its schema."""
    return str(TASKS.path)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
