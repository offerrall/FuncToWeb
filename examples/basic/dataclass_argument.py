"""A dataclass parameter is a group of fields, one per attribute."""

from dataclasses import dataclass

from func_to_web import run


@dataclass
class Rectangle:
    """A rectangle measured in centimeters."""

    width: int
    height: int


def area(rectangle: Rectangle) -> str:
    """Compute the area of a rectangle."""
    return f"{rectangle.width * rectangle.height} cm2"


if __name__ == "__main__":
    run(area, title="Geometry")
