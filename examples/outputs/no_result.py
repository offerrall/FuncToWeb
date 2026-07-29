"""A function without a result still produces one output: "Done"."""

from func_to_web import run


def archive_order(reference: str) -> None:
    """Do the work and return nothing, which the web shows as "Done"."""
    print(f"Archiving order {reference}")


def clear_queue(name: str) -> list[str]:
    """Return an empty collection, which also shows "Done"."""
    print(f"Clearing queue {name}")

    return []


if __name__ == "__main__":
    run([archive_order, clear_queue], title="No result")
