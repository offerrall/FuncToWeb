"""An opening stays inside its space, so it keeps the same theme."""

from typing import Annotated

from func_to_web import Choices, Min, OpenForm, run

LOANS: dict[str, int] = {"L-100": 7, "L-200": 14, "L-300": 3}

Reference = Annotated[str, Choices(values=tuple(LOANS))]


def extend_loan(reference: str, days: Annotated[int, Min(1)]) -> str:
    """Extend a loan to a new number of days."""
    if reference not in LOANS:
        raise ValueError(f"unknown loan: {reference}")

    LOANS[reference] = days

    return f"Loan {reference} now runs for {days} days."


def open_loan(
    reference: Reference = "L-100",
) -> Annotated[dict, OpenForm(extend_loan, hidden=("reference",))]:
    """Open the extension form of a loan, on the theme of the space.

    The opening is an ordinary GET on the target page of this same application,
    so the target is served with the theme the space was built with and the
    navigation does not change the palette.
    """
    return {"reference": reference, "days": LOANS[reference]}


if __name__ == "__main__":
    run([open_loan, extend_loan], title="Library", theme="dark")
