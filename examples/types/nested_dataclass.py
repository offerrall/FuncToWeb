"""Nested dataclasses: a dataclass whose fields are dataclasses too."""

from dataclasses import dataclass, field
from typing import Annotated

from func_to_web import Label, Max, Min, Pattern, run


@dataclass
class Address:
    """A postal address."""

    street: Annotated[str, Min(3), Max(60)]
    city: Annotated[str, Min(2), Max(40)]
    postal_code: Annotated[str, Pattern(r"^[0-9]{5}$"), Label("Postal code")]


@dataclass
class Contact:
    """Someone to call, with an optional second address."""

    name: Annotated[str, Min(2), Max(40)]
    main: Address = field(
        default_factory=lambda: Address(
            street="Main street 1", city="Springfield", postal_code="28001"
        )
    )
    billing: Address | None = None


def contact_card(contact: Annotated[Contact, Label("Contact")]) -> str:
    """Render a contact whose addresses are validated at every level."""
    lines = [
        f"{contact.name}",
        f"main: {contact.main.street}, {contact.main.city}",
    ]

    if contact.billing is not None:
        lines.append(
            f"billing: {contact.billing.street}, {contact.billing.city}"
        )

    return " | ".join(lines)


if __name__ == "__main__":
    run(contact_card, title="Nested dataclass")
