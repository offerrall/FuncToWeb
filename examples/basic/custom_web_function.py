"""WebFunction publishes a callable under a name, description and slug."""

from func_to_web import WebFunction, run


def celsius_to_fahrenheit(celsius: float) -> str:
    """Convert Celsius degrees into Fahrenheit degrees."""
    return f"{celsius * 9 / 5 + 32:.1f} F"


def build_function() -> WebFunction:
    """Publish the converter with its own name, description and slug."""
    return WebFunction(
        celsius_to_fahrenheit,
        name="Celsius to Fahrenheit",
        description="Turn a temperature into its Fahrenheit value.",
        slug="c2f",
    )


if __name__ == "__main__":
    run(build_function(), title="Temperatures")
