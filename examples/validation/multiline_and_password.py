"""Rows makes a textarea and IsPassword only masks what is on screen."""

from typing import Annotated

from func_to_web import IsPassword, Max, Min, Placeholder, Rows, run


def publish_note(
    body: Annotated[
        str,
        Rows(6),
        Min(1),
        Max(2000),
        Placeholder("Write the release note here"),
    ],
    token: Annotated[str, IsPassword(), Min(8), Max(64)],
) -> str:
    """Publish a release note using a token.

    Rows turns the text field into a textarea of that height. IsPassword only
    masks the characters on screen: it does not encrypt the value, does not
    hide it from the request body, and does not keep it out of logs or
    browser history. Treat it as presentation, never as protection.
    """
    return f"{len(body)} chars published with a {len(token)}-char token"


if __name__ == "__main__":
    run(publish_note, title="Multiline and masked text")
