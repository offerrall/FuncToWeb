"""A polars DataFrame is a table output, exactly like the pandas one."""

from typing import Annotated

import polars as pl

from func_to_web import Choices, Max, Min, run


def inventory_report(
    rows: Annotated[int, Min(1), Max(50)] = 8,
    warehouse: Annotated[
        str, Choices(values=("madrid", "lisbon", "porto"))
    ] = "madrid",
    only_low_stock: bool = False,
) -> pl.DataFrame:
    """Build an in-memory inventory report as a polars DataFrame."""
    frame = pl.DataFrame(
        {
            "item": [f"ITEM-{index + 1:03d}" for index in range(rows)],
            "warehouse": [warehouse] * rows,
            "stock": [(index * 23 + 5) % 90 for index in range(rows)],
            "weight_kg": [round(0.25 + index * 1.4, 3)
                          for index in range(rows)],
        }
    )
    frame = frame.with_columns(
        (pl.col("stock") * pl.col("weight_kg")).round(2).alias("total_kg")
    )

    if only_low_stock:
        frame = frame.filter(pl.col("stock") < 30)

    return frame


if __name__ == "__main__":
    run(inventory_report, title="Polars DataFrame")
