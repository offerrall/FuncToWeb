"""hidden carries a parameter into the opened form without showing it."""

from typing import Annotated

from func_to_web import Choices, Min, OpenForm, run

INVOICES: dict[str, float] = {
    "INV-001": 120.5,
    "INV-002": 80.0,
    "INV-003": 240.75,
}

Reference = Annotated[str, Choices(values=tuple(INVOICES))]

Method = Annotated[str, Choices(values=("card", "transfer", "cash"))]


def register_payment(
    reference: str,
    amount: Annotated[float, Min(0.0)],
    method: Method = "card",
) -> str:
    """Register the payment of an invoice."""
    if reference not in INVOICES:
        raise ValueError(f"unknown invoice: {reference}")

    pending = INVOICES[reference] - amount

    return f"{reference} paid {amount:.2f} by {method}, pending {pending:.2f}."


def pay_invoice(
    reference: Reference = "INV-001",
) -> Annotated[dict, OpenForm(register_payment, hidden=("reference",))]:
    """Open the payment form of an invoice, without showing its reference."""
    return {"reference": reference, "amount": INVOICES[reference]}


if __name__ == "__main__":
    run([pay_invoice, register_payment], title="Billing")
