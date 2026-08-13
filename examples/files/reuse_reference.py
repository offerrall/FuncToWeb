"""One transfer, many executions: the reference outlives the invocation."""

from pathlib import Path
from typing import Annotated

from func_to_web import FileHint, Label, Max, Min, run

TextFile = Annotated[str, FileHint(extensions=(".txt", ".md"))]


def head_of_report(
    document: Annotated[TextFile, Label("Report")],
    lines: Annotated[int, Min(1), Max(50), Label("Lines to show")] = 5,
    upper: bool = False,
) -> str:
    """Show the first lines of a stored report, tuning the run each time.

    The bytes travel once. Submitting again with another number of lines
    sends only the JSON form, with the very same reference in it, so trying
    several settings over a heavy file never moves the file again. Every run
    resolves that reference against the storage before the function is
    called, which is what refuses one that names nothing; the file itself is
    not opened, weighed or filtered again on the way in.
    """
    content = Path(document).read_text(encoding="utf-8")
    head = "\n".join(content.splitlines()[:lines])

    return head.upper() if upper else head


if __name__ == "__main__":
    run(head_of_report, title="Reuse reference")
