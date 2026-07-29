"""An exception is never an output: it travels as an error, not a result."""

from func_to_web import run


def divide(dividend: float, divisor: float) -> float:
    """Divide two numbers; a zero divisor raises ZeroDivisionError."""
    return dividend / divisor


def load_profile(user: str) -> str:
    """Read a profile and raise ValueError when the user is unknown."""
    profiles = {"ana": "admin", "leo": "editor"}

    if user not in profiles:
        raise ValueError(f"unknown user: {user}")

    return f"{user}: {profiles[user]}"


if __name__ == "__main__":
    run([divide, load_profile], title="Errors")
