"""A list of dataclasses: repeatable rows, each one validated."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from func_to_web import Description, Label, Max, Min, run


class Unit(Enum):
    """How a line item is counted."""

    PIECE = "piece"
    KILOGRAM = "kilogram"
    LITRE = "litre"


@dataclass
class LineItem:
    """One row of an order."""

    product: Annotated[str, Min(2), Max(40)]
    quantity: Annotated[float, Min(0.01), Max(1000.0)]
    unit_price: Annotated[float, Min(0.0), Max(10000.0), Label("Unit price")]
    unit: Unit = Unit.PIECE


def order_total(
    items: Annotated[
        list[LineItem],
        Min(1),
        Max(20),
        Label("Line items"),
        Description("Add one row per product"),
    ],
) -> str:
    """Add up an order given as a list of dataclasses."""
    lines = [
        f"{item.quantity:g} {item.unit.value} of {item.product} "
        f"= {item.quantity * item.unit_price:.2f}"
        for item in items
    ]
    total = sum(item.quantity * item.unit_price for item in items)

    return " | ".join([*lines, f"TOTAL {total:.2f}"])


if __name__ == "__main__":
    run(order_total, title="List of dataclasses")
