"""A dataclass parameter arrives as a real, already validated instance."""

from dataclasses import dataclass
from typing import Annotated

from func_to_web import Description, Label, Max, Min, run

Side = Annotated[float, Min(0.1), Max(500.0)]


@dataclass
class Rectangle:
    """A rectangle measured in centimetres."""

    width: Side
    height: Side
    label: Annotated[str, Max(30), Label("Label")] = "unnamed"


def rectangle_report(
    shape: Annotated[Rectangle, Description("Grouped as a nested object")],
) -> str:
    """Compute area and perimeter of a rectangle given as a dataclass."""
    area = shape.width * shape.height
    perimeter = 2 * (shape.width + shape.height)

    return f"{shape.label}: area {area:.2f} cm2, perimeter {perimeter:.2f} cm"


if __name__ == "__main__":
    run(rectangle_report, title="Dataclass input")
