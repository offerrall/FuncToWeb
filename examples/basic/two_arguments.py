"""One parameter is one field, and a default arrives already filled in."""

from func_to_web import run


def repeat(text: str, times: int = 3) -> str:
    """Repeat a text as many times as asked."""
    lines = [f"{index}. {text}" for index in range(1, times + 1)]
    return "\n".join(lines)


if __name__ == "__main__":
    run(repeat, title="Repeat")
