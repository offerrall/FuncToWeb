"""A nested list: validation reaches every level of the structure."""

from typing import Annotated

from func_to_web import Label, Max, Min, run

Cell = Annotated[float, Min(-1000.0), Max(1000.0)]
Row = Annotated[list[Cell], Min(1), Max(8)]


def matrix_totals(
    rows: Annotated[list[Row], Min(1), Max(8), Label("Matrix rows")],
) -> str:
    """Add up a matrix declared as a list of lists of numbers."""
    widths = {len(row) for row in rows}

    if len(widths) != 1:
        raise ValueError("every row must have the same number of cells")

    totals = [sum(row) for row in rows]
    columns = [sum(column) for column in zip(*rows, strict=True)]

    return (
        f"rows {len(rows)} x columns {widths.pop()} | "
        f"row totals {totals} | column totals {columns} | "
        f"grand total {sum(totals)}"
    )


if __name__ == "__main__":
    run(matrix_totals, title="Nested list")
