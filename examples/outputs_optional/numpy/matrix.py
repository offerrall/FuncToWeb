"""A 2D numpy array is a table output, with generated headers."""

from typing import Annotated

import numpy as np

from func_to_web import Choices, Max, Min, run

Size = Annotated[int, Min(2), Max(12)]


def multiplication_table(
    rows: Size = 6,
    columns: Size = 6,
    operation: Annotated[
        str, Choices(values=("multiply", "add", "power"))
    ] = "multiply",
) -> np.ndarray:
    """Build a 2D numpy array, rendered as a table with generated headers."""
    left = np.arange(1, rows + 1).reshape(rows, 1)
    right = np.arange(1, columns + 1).reshape(1, columns)

    if operation == "add":
        return left + right

    if operation == "power":
        return left**right

    return left * right


if __name__ == "__main__":
    run(multiplication_table, title="Numpy matrix")
