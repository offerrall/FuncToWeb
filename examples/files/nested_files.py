"""A file field is resolved at any depth of the structure."""

from pathlib import Path
from typing import Annotated

from func_to_web import IsPathFile, Label, Max, Min, run

TextFile = Annotated[str, IsPathFile(extensions=(".txt", ".md"))]

Groups = Annotated[
    list[Annotated[list[TextFile], Min(1), Max(3)]],
    Min(2),
    Max(2),
    Label("Two groups of documents"),
]


def compare_groups(groups: Groups) -> str:
    """Compare the total length of two groups of documents.

    Nothing special is needed for a file inside a list of lists: the same
    pass that prepares dates, floats and enums walks the whole structure and
    turns every value declared as a file into a local path, one by one.
    """
    totals = [
        sum(len(Path(item).read_text(encoding="utf-8")) for item in group)
        for group in groups
    ]
    first, second = totals

    verdict = "tie" if first == second else (
        "first group is longer" if first > second else
        "second group is longer"
    )

    return f"{first} vs {second} characters: {verdict}"


if __name__ == "__main__":
    run(compare_groups, title="Nested files")
