"""Users — a mini-app where a file field travels the whole cycle.

The model is one dataclass, photo included: the resolver reaches the file
field inside it, the function receives the stored file's local path in
user.photo, and what the host keeps is the reference from the transport —
the reusable half: editing opens the form with the photo already in place,
and no byte is uploaded again.

The host serves each photo through an endpoint of its own, from the path
it kept — after a run, custody of the file belongs to the application.

Run:  python users.py
Open: http://127.0.0.1:8000/ (or /tools/doc, /api/users)
"""

from dataclasses import dataclass
from itertools import count
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn

from func_to_web import Email, IsPathFile, Label, Min, Max, router_of


@dataclass
class User:
    name: Annotated[str, Min(1), Max(60), Label("Name")]
    email: Email
    photo: Annotated[str, IsPathFile(extensions=(".png", ".jpg", ".jpeg", ".webp"))]


USERS: dict[int, User] = {}
_ids = count(1)


def create_user(user: User) -> str:
    """Create a user with their photo."""
    user_id = next(_ids)
    USERS[user_id] = user
    return f"User {user_id} created"


def edit_user(user_id: int, user: User) -> str:
    """Edit a user; the photo needs no re-upload if unchanged."""
    if user_id not in USERS:
        raise KeyError(f"no user {user_id}")
    USERS[user_id] = user
    return "User updated"


def delete_user(user_id: int) -> str:
    """Delete a user."""
    if USERS.pop(user_id, None) is None:
        raise KeyError(f"no user {user_id}")
    return "User deleted"


PAGE = """<!doctype html>
<meta charset="utf-8">
<title>Users</title>
<style>
body { font: 16px system-ui; max-width: 40rem; margin: 3rem auto; }
li { display: flex; gap: .8rem; align-items: center; margin: .6rem 0; }
li img { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; }
li span { flex: 1; }
small { opacity: .6; }
</style>

<h1>Users</h1>
<p>The photo travels once: editing a user opens the form with it in place.</p>

<button id="new" type="button">New user</button>
<ul id="users"></ul>

<script type="module">
import { openModal } from "/tools/static/sdk.js";

const list = document.getElementById("users");

async function users() {
    const response = await fetch("/api/users");

    return response.json();
}

async function run(url, prefill, hidden) {
    const modal = openModal(url, { prefill, hidden, closeOnResult: true });
    const { completed } = await modal.closed;

    if (completed) await refresh();
}

function row(user) {
    const item = document.createElement("li");
    const photo = document.createElement("img");
    const label = document.createElement("span");

    photo.src = `/api/photo/${user.user_id}?v=${encodeURIComponent(user.user.photo)}`;
    label.innerHTML = "<b></b><br><small></small>";
    label.querySelector("b").textContent = user.user.name;
    label.querySelector("small").textContent = user.user.email;

    const edit = document.createElement("button");
    edit.type = "button";
    edit.textContent = "Edit";
    edit.addEventListener("click", () => run(
        "/tools/edit_user",
        { user_id: user.user_id, user: user.user },
        ["user_id"],
    ));

    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Delete";
    remove.addEventListener("click", () => run(
        "/tools/delete_user", { user_id: user.user_id }, ["user_id"]));

    item.append(photo, label, edit, remove);

    return item;
}

async function refresh() {
    list.replaceChildren(...(await users()).map(row));
}

document.getElementById("new").addEventListener(
    "click", () => run("/tools/create_user"));

await refresh();
</script>
"""

app = FastAPI()
app.include_router(router_of([create_user, edit_user, delete_user]), prefix="/tools")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """Serve the host page that opens each function in a modal."""
    return PAGE


@app.get("/api/users")
def list_users() -> list[dict]:
    return [
        {
            "user_id": i,
            "user": {"name": u.name, "email": u.email, "photo": Path(u.photo).name},
        }
        for i, u in sorted(USERS.items())
    ]


@app.get("/api/photo/{user_id}")
def photo(user_id: int) -> FileResponse:
    """Serve a user's photo from the path the application kept."""
    return FileResponse(USERS[user_id].photo)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)