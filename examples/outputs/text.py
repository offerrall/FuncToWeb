"""Any value that is not an image, a table or a download becomes text."""

from func_to_web import run


def describe_order(reference: str, units: int) -> str:
    """Summarise an order as a single line of text."""
    return f"Order {reference}: {units} units"


def stock_left(units: int, sold: int) -> int:
    """Return a number, shown with its str() representation."""
    return units - sold


def is_available(units: int, sold: int) -> bool:
    """Return a boolean, shown as True or False."""
    return units > sold


if __name__ == "__main__":
    run([describe_order, stock_left, is_available], title="Text outputs")
