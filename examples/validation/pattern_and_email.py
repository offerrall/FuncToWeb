"""Pattern is a full-match regex, and Email is that idea prepackaged."""

from typing import Annotated

from func_to_web import Email, Max, Min, Pattern, run

INVOICE_CODE = r"INV-[0-9]{4}-[0-9]{3}"


def queue_invoice(
    code: Annotated[
        str,
        Pattern(INVOICE_CODE, message="Codes look like INV-2026-014"),
    ],
    recipient: Email,
    subject: Annotated[str, Min(3), Max(60)] = "Your invoice",
) -> str:
    """Queue an invoice, checking both text formats before any work starts.

    Pattern takes a full-match regex and an optional message that replaces the
    default one. Email is the same idea prepackaged: a str with a format
    filter, not a real address validator.
    """
    return f"{code} queued for {recipient} - {subject}"


if __name__ == "__main__":
    run(queue_invoice, title="Text patterns")
