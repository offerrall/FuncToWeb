from typing import TypedDict


class TextOutput(TypedDict):
    type: str
    value: str


def text_output(value: str) -> TextOutput:
    return {
        "type": "text",
        "value": value,
    }
