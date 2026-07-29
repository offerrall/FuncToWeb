"""Optional parameters: `X | None` is drawn as a toggle."""

from typing import Annotated

from func_to_web import Label, Max, Min, OptionalToggle, run


def render_invoice(
    customer: Annotated[str, Min(2), Max(60)],
    amount: Annotated[float, Min(0.0)],
    discount: Annotated[float, Min(0.0), Max(90.0)] | None = None,
    note: Annotated[str, Max(120), Label("Note"), OptionalToggle(True)]
    | None = "Thanks for your order",
) -> str:
    """Apply an optional discount and append an optional note."""
    total = amount if discount is None else amount * (1 - discount / 100)
    lines = [f"{customer}: {total:.2f}"]

    if note is not None:
        lines.append(note)

    return " | ".join(lines)


if __name__ == "__main__":
    run(render_invoice, title="Optional value")
