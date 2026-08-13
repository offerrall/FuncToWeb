"""list[File] is the multiple selection, and its bounds count files."""

from pathlib import Path
from typing import Annotated

from func_to_web import FileHint, Label, Max, Min, run

TextFile = Annotated[str, FileHint(extensions=(".txt", ".md"))]

Documents = Annotated[
    list[TextFile],
    Min(1),
    Max(3),
    Label("Documents to merge"),
]


def merge_documents(documents: Documents, separator: str = "---") -> str:
    """Join between one and three uploaded documents into a single text.

    Min and Max on the list are limits on how many files may be chosen, not
    on their size. Every chosen file mints its own reference and travels on
    its own, and the function receives the paths in the declared order.
    """
    parts = [Path(item).read_text(encoding="utf-8") for item in documents]

    return f"\n{separator}\n".join(parts)


if __name__ == "__main__":
    run(merge_documents, title="Multiple files")
