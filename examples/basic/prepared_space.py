"""WebFunctions is the space built by hand, carrying its own title."""

from func_to_web import WebFunction, WebFunctions, run


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def divide(a: float, b: float = 1.0) -> float:
    """Divide the first number by the second one."""
    return a / b


def build_space() -> WebFunctions:
    """Prepare the space by hand, as a tuple of WebFunction plus a title."""
    return WebFunctions(
        (
            WebFunction(add),
            WebFunction(divide, name="Division", slug="division"),
        ),
        title="Internal tools",
    )


if __name__ == "__main__":
    run(build_space())
