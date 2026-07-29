"""Extra stores namespaced key/value pairs on a field, uninterpreted."""

from typing import Annotated

from func_to_web import Email, Extra, Max, Min, run


def subscribe(
    address: Annotated[
        Email, Extra("funtoweb.example.field", "primary-email")
    ],
    source: Annotated[
        str,
        Min(2),
        Max(30),
        Extra("funtoweb.example.field", "referrer"),
        Extra("funtoweb.example.group", "acquisition"),
    ] = "web",
) -> str:
    """Attach namespaced key/value metadata to two fields.

    Extra is a storage slot, not a rendering instruction: the key must be
    namespaced so several wrappers can annotate one field without clashing,
    and the schema keeps the pair without ever interpreting it. It changes
    the page only when some wrapper chooses to read that key.
    """
    return f"{address} subscribed from {source}"


if __name__ == "__main__":
    run(subscribe, title="Extra metadata")
