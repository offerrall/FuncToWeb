"""capture_prints is decided by the space and overridden per function."""

from typing import Annotated

from func_to_web import Max, Min, WebFunction, run


def audited(steps: Annotated[int, Min(1), Max(10)] = 3) -> str:
    """Inherit the policy of the space, so its prints are streamed."""
    for index in range(steps):
        print(f"audited step {index}")

    return f"{steps} audited step(s)"


def silent(steps: Annotated[int, Min(1), Max(10)] = 3) -> str:
    """Print only to the server console: the browser sees no print event."""
    for index in range(steps):
        print(f"silent step {index}")

    return f"{steps} silent step(s)"


if __name__ == "__main__":
    run(
        [
            WebFunction(audited),
            WebFunction(silent, capture_prints=False),
        ],
        title="Capture policy",
        capture_prints=True,
    )
