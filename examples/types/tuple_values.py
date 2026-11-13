"""A tuple parameter is a list in the form and a real tuple in the function."""

from typing import Annotated

from func_to_web import Label, Max, Min, run

Channel = Annotated[float, Min(0.0), Max(1.0)]


def blend(
    color: Annotated[tuple[Channel, Channel, Channel], Label("RGB")] = (1.0, 0.5, 0.0),
    weights: Annotated[tuple[float, ...], Min(1), Max(5)] = (1.0,),
) -> str:
    """Scale an RGB colour by the mean of one to five weights."""
    weight = sum(weights) / len(weights)
    red, green, blue = (round(channel * weight, 3) for channel in color)

    return f"({red}, {green}, {blue}) with weight {weight:.2f}"


if __name__ == "__main__":
    run(blend, title="Tuple values")
