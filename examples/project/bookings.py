"""Bookings — a dataclass that is the whole form and the whole rulebook.

One model holds the rest of the vocabulary: a date and two times, the room as
an enum, the attendees as a slider between its own bounds, a checkbox and a
note that is there only when its switch is on. Nothing is described twice — the
picker, the closed list of rooms, the track and the switch are read from those
annotations, and so is what /doc publishes.

The rule that no single field can state lives with them, in __post_init__: a
booking that ends before it starts, or that seats more people than the room
holds, is not built. It surfaces as a clean 422 in the form and in the API
alike, because it belongs to the model and not to a handler — a direct call to
/invoke cannot skip what the browser was stopped by.

Editing a row reopens the same model as a prefill, in the transport format:
dates and times as ISO text, and the room as the name of its member.

Run:  python bookings.py
Open: http://127.0.0.1:8000/ (or /tools/doc, /api/bookings)
"""

from dataclasses import dataclass
from datetime import date, time
from enum import Enum
from itertools import count
from typing import Annotated

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from func_to_web import Label, Max, Min, OptionalToggle, Slider, app_of


class Room(Enum):
    FOCUS = 4
    BOARD = 12
    TRAINING = 20


@dataclass
class Booking:
    day: Annotated[date, Label("Day")]
    start: Annotated[time, Label("From")]
    end: Annotated[time, Label("To")]
    room: Annotated[Room, Label("Room")] = Room.BOARD
    attendees: Annotated[int, Min(1), Max(20), Slider(), Label("Attendees")] = 6
    catering: Annotated[bool, Label("Catering")] = False
    notes: Annotated[
        str | None,
        Max(200),
        OptionalToggle(False),
        Label("Notes"),
    ] = None

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("end must be after start")

        if self.attendees > self.room.value:
            raise ValueError(f"{self.room.name} seats {self.room.value} people")


BOOKINGS: dict[int, Booking] = {}
_ids = count(1)


def create_booking(booking: Booking) -> str:
    """Book a room."""
    booking_id = next(_ids)
    BOOKINGS[booking_id] = booking

    return f"Booking {booking_id} created"


def edit_booking(booking_id: int, booking: Booking) -> str:
    """Edit a booking."""
    if booking_id not in BOOKINGS:
        raise KeyError(f"no booking {booking_id}")

    BOOKINGS[booking_id] = booking

    return "Booking updated"


def delete_booking(booking_id: int) -> str:
    """Delete a booking."""
    if BOOKINGS.pop(booking_id, None) is None:
        raise KeyError(f"no booking {booking_id}")

    return "Booking deleted"


PAGE = """<!doctype html>
<meta charset="utf-8">
<title>Bookings</title>
<style>
body { font: 16px system-ui; max-width: 42rem; margin: 3rem auto; }
li { display: flex; gap: .5rem; align-items: center; margin: .4rem 0; }
li span { flex: 1; }
small { opacity: .6; }
</style>

<h1>Bookings</h1>
<p>A booking that ends before it starts never reaches the calendar.</p>

<button id="new" type="button">New booking</button>
<ul id="bookings"></ul>

<script type="module">
import { openModal } from "/tools/static/sdk.js";

const list = document.getElementById("bookings");

async function bookings() {
    const response = await fetch("/api/bookings");

    return response.json();
}

async function run(url, prefill, hidden) {
    const modal = openModal(url, { prefill, hidden, closeOnResult: true });
    const { completed } = await modal.closed;

    if (completed) await refresh();
}

function row(entry) {
    const item = document.createElement("li");
    const label = document.createElement("span");
    const booking = entry.booking;

    label.innerHTML = "<b></b><br><small></small>";
    label.querySelector("b").textContent =
        `${booking.day} ${booking.start}-${booking.end} in ${booking.room}`;
    label.querySelector("small").textContent =
        `${booking.attendees} attendee(s)` +
        (booking.catering ? ", catering" : "") +
        (booking.notes === null ? "" : ` — ${booking.notes}`);

    const edit = document.createElement("button");
    edit.type = "button";
    edit.textContent = "Edit";
    edit.addEventListener("click", () => run(
        "/tools/edit_booking",
        { booking_id: entry.booking_id, booking },
        ["booking_id"],
    ));

    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Delete";
    remove.addEventListener("click", () => run(
        "/tools/delete_booking", { booking_id: entry.booking_id }, ["booking_id"]));

    item.append(label, edit, remove);

    return item;
}

async function refresh() {
    list.replaceChildren(...(await bookings()).map(row));
}

document.getElementById("new").addEventListener(
    "click", () => run("/tools/create_booking"));

await refresh();
</script>
"""

app = FastAPI()
app.mount("/tools", app_of([create_booking, edit_booking, delete_booking]))


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """Serve the host page that opens each function in a modal."""
    return PAGE


@app.get("/api/bookings")
def list_bookings() -> list[dict]:
    return [
        {
            "booking_id": i,
            "booking": {
                "day": b.day.isoformat(),
                "start": b.start.isoformat(),
                "end": b.end.isoformat(),
                "room": b.room.name,
                "attendees": b.attendees,
                "catering": b.catering,
                "notes": b.notes,
            },
        }
        for i, b in sorted(BOOKINGS.items(), key=lambda entry: (
            entry[1].day, entry[1].start, entry[0]))
    ]


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
