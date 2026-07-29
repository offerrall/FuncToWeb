"""Min, Max and MultipleOf bound a number in the page and in the schema."""

from typing import Annotated

from func_to_web import Max, Min, MultipleOf, run


def quote_pallet(
    boxes: Annotated[int, Min(12), Max(480), MultipleOf(12)],
    box_weight_kg: Annotated[float, Min(0.0, exclusive=True), Max(25.0)],
) -> str:
    """Quote a pallet: boxes ship in dozens and each one has a weight cap.

    The bounds live in the signature, so the form refuses an out-of-range
    value and the schema refuses it again before the function runs.
    """
    total = boxes * box_weight_kg

    return f"{boxes} boxes, {total:.2f} kg on the pallet"


if __name__ == "__main__":
    run(quote_pallet, title="Numeric limits")
