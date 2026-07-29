"""Scalar parameters: str, int, float and bool."""

from typing import Annotated

from func_to_web import Description, Label, Max, Min, Placeholder, Step, run


def describe_product(
    name: Annotated[str, Min(2), Max(40), Placeholder("Blue notebook")],
    units: Annotated[int, Min(1), Max(999), Label("Units in stock")],
    price: Annotated[float, Min(0.0), Max(10000.0), Step(0.01)],
    on_sale: Annotated[
        bool, Description("Apply the seasonal discount")
    ] = False,
) -> str:
    """Build a one-line summary out of the four scalar types."""
    final_price = price * 0.8 if on_sale else price
    total = final_price * units

    return (
        f"{name}: {units} units at {final_price:.2f} each, total {total:.2f}"
    )


if __name__ == "__main__":
    run(describe_product, title="Scalar types")
