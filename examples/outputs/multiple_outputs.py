"""A list or a tuple means several outputs, one per element and in order."""

from func_to_web import run


def split_tags(tags: str) -> list[str]:
    """Return one text output per tag of a comma separated list."""
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


def order_summary(units: int, price: float) -> tuple[str, float, bool]:
    """Return three outputs: a label, the total and whether it is large."""
    total = units * price

    return f"{units} units at {price:.2f}", total, total > 100


if __name__ == "__main__":
    run([split_tags, order_summary], title="Multiple outputs")
