from typing import Literal, get_args

Theme = Literal["system", "light", "dark"]
"""The three themes a space can be served with; "system" follows the OS."""

THEMES: tuple[Theme, ...] = get_args(Theme)


def checked_theme(value: object) -> Theme:
    if type(value) is not str:
        raise TypeError("theme must be str")

    if value not in THEMES:
        raise ValueError(
            f"theme must be one of {', '.join(THEMES)}; got {value!r}"
        )

    return value


def theme_attribute(theme: Theme) -> str:
    if theme == "system":
        return ""

    return f' data-pth-theme="{theme}"'
