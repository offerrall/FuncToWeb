"""Several files in one Download need a callable filename, one name each."""

from pathlib import Path
from tempfile import mkdtemp
from typing import Annotated

from func_to_web import Download, run


def part_name(value: object, index: int) -> str:
    """Name every file after its position inside this Download."""
    return f"part-{index + 1}.txt"


Parts = Annotated[list[Path], Download(part_name)]


def split_lines(text: str) -> tuple[str, Parts]:
    """Return how many parts were written and one file per line."""
    folder = Path(mkdtemp())
    paths = []

    for index, line in enumerate(text.splitlines()):
        path = folder / f"line-{index}.txt"

        with path.open("w", encoding="utf-8") as file:
            file.write(line)

        paths.append(path)

    return f"{len(paths)} parts", paths


if __name__ == "__main__":
    run(split_lines, title="Several downloads")
