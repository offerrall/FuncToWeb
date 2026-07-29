"""A list of functions is one space: a page each and an index for all."""

from func_to_web import run


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def divide(a: float, b: float = 1.0) -> float:
    """Divide the first number by the second one."""
    return a / b


def percentage(value: float, total: float) -> str:
    """Express a value as a percentage of a total."""
    return f"{value / total * 100:.2f} %"


if __name__ == "__main__":
    run([add, divide, percentage], title="Internal tools")
