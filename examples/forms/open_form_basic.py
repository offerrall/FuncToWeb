"""OpenForm hands the browser to another form, already filled in."""

from typing import Annotated

from func_to_web import OpenForm, run

CUSTOMERS: dict[int, dict[str, str]] = {
    1: {"name": "Ana Ruiz", "city": "Valencia"},
    2: {"name": "Beto Lima", "city": "Porto"},
    3: {"name": "Cira Nunez", "city": "Bogota"},
}


def edit_customer(customer_id: int, name: str, city: str) -> str:
    """Save the new details of a customer."""
    if customer_id not in CUSTOMERS:
        raise ValueError(f"unknown customer: {customer_id}")

    CUSTOMERS[customer_id] = {"name": name, "city": city}

    return f"Customer {customer_id} saved as {name} ({city})."


def load_customer(
    customer_id: int = 1,
) -> Annotated[dict, OpenForm(edit_customer)]:
    """Open the editor of a customer with its current details."""
    customer = CUSTOMERS.get(customer_id)

    if customer is None:
        raise ValueError(f"unknown customer: {customer_id}")

    return {"customer_id": customer_id, **customer}


if __name__ == "__main__":
    run([load_customer, edit_customer], title="Customers")
