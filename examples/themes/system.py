"""The system theme is the default: the operating system decides."""

from func_to_web import run


def theme_sample(text: str = "The quick brown fox") -> str:
    """Show this page with the system theme, the default one.

    No theme attribute is stamped on the document, so the widgets stylesheet
    decides light or dark from the operating system preference, in CSS and
    before the first paint. The same URL looks different on two machines.
    """
    return f"{text}, drawn by the theme of this space."


if __name__ == "__main__":
    run(theme_sample, title="Theme demo", theme="system")
