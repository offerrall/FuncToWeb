from typing import TypedDict


class FormOutput(TypedDict):
    type: str
    href: str


def form_output(href: str) -> FormOutput:
    return {
        "type": "form",
        "href": href,
    }
