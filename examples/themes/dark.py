"""theme='dark' forces the dark palette on every page of the space."""

from func_to_web import run


def theme_sample(text: str = "The quick brown fox") -> str:
    """Show this page with the dark theme, forced for everyone.

    The server stamps the dark theme attribute on the document of every
    page of the space, so the palette travels in the initial markup and the
    operating system preference is ignored, with no flash either.
    """
    return f"{text}, drawn by the theme of this space."


if __name__ == "__main__":
    run(theme_sample, title="Theme demo", theme="dark")
