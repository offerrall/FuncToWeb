"""Nested collections are flattened to any depth, keeping their order."""

from func_to_web import run


def multiplication_table(number: int, rows: int) -> list:
    """Return nested lists whose leaves become one text output each."""
    header = f"Table of {number}"

    body = [
        [f"{number} x {row} = {number * row}"]
        for row in range(1, rows + 1)
    ]

    return [header, body, ["end of table"]]


if __name__ == "__main__":
    run(multiplication_table, title="Nested outputs")
