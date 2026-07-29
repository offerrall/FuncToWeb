"""A pandas DataFrame is a table output, with its own columns as headers."""

from typing import Annotated

import pandas as pd

from func_to_web import Choices, Max, Min, run


def sales_report(
    rows: Annotated[int, Min(1), Max(50)] = 8,
    region: Annotated[
        str, Choices(values=("north", "south", "east"))
    ] = "north",
    sort_by_revenue: bool = True,
) -> pd.DataFrame:
    """Build an in-memory sales report and return it as a pandas DataFrame."""
    frame = pd.DataFrame(
        {
            "product": [f"SKU-{index + 1:03d}" for index in range(rows)],
            "region": [region] * rows,
            "units": [(index * 37 + 11) % 120 + 1 for index in range(rows)],
            "price": [round(9.5 + index * 3.25, 2) for index in range(rows)],
        }
    )
    frame["revenue"] = (frame["units"] * frame["price"]).round(2)

    if sort_by_revenue:
        frame = frame.sort_values("revenue", ascending=False)

    return frame


if __name__ == "__main__":
    run(sales_report, title="Pandas DataFrame")
