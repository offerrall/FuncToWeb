"""The values of an opening can be a dataclass instead of a dict."""

from dataclasses import dataclass
from datetime import date
from typing import Annotated

from func_to_web import Min, OpenForm, run


@dataclass
class Booking:
    """One booking, with a field per parameter of the edit form."""

    booking_id: int
    guest: str
    nights: int
    arrival: date


BOOKINGS: dict[int, Booking] = {
    10: Booking(10, "Ana Ruiz", 3, date(2026, 8, 14)),
    11: Booking(11, "Beto Lima", 7, date(2026, 9, 1)),
}


def edit_booking(
    booking_id: int,
    guest: str,
    nights: Annotated[int, Min(1)],
    arrival: date,
) -> str:
    """Save the new state of a booking."""
    BOOKINGS[booking_id] = Booking(booking_id, guest, nights, arrival)

    return f"Booking {booking_id} saved for {guest}: {nights} nights."


def load_booking(
    booking_id: int = 10,
) -> Annotated[Booking, OpenForm(edit_booking)]:
    """Open the editor of a booking, returning the record itself."""
    booking = BOOKINGS.get(booking_id)

    if booking is None:
        raise ValueError(f"unknown booking: {booking_id}")

    return booking


if __name__ == "__main__":
    run([load_booking, edit_booking], title="Bookings")
