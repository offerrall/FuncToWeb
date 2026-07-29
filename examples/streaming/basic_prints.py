"""What a function prints travels to the browser while it runs."""

from typing import Annotated

from func_to_web import Max, Min, run


def announce(name: str = "world") -> str:
    """Print a single line before returning."""
    print(f"hello {name}")

    return f"greeted {name}"


def checklist(items: Annotated[int, Min(1), Max(20)] = 4) -> str:
    """Print one line per item and report the total."""
    for index in range(1, items + 1):
        print(f"step {index} of {items} done")

    return f"{items} step(s) reported"


if __name__ == "__main__":
    run([announce, checklist], title="Basic prints")
