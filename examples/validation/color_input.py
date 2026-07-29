"""Color is a str carrying the hex pattern, and its widget is a picker."""

from typing import Annotated

from func_to_web import COLOR_PATTERN, Color, Label, Pattern, run


def preview_theme(
    background: Annotated[Color, Label("Background")] = "#1e1e2e",
    accent: Annotated[
        str, Pattern(COLOR_PATTERN), Label("Accent")
    ] = "#f38ba8",
) -> str:
    """Preview a two-colour theme.

    Color is not a new type: it is a str carrying the hex pattern, so writing
    that same COLOR_PATTERN by hand gives the same contract and the same
    colour picker. Python receives a plain str either way.
    """
    return f"background {background} with accent {accent}"


if __name__ == "__main__":
    run(preview_theme, title="Colour inputs")
