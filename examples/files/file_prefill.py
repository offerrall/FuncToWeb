"""A planted file opens a form as an existing file, with nothing pending."""

from pathlib import Path
from typing import Annotated

from func_to_web import FileHint, Label, Max, Min, OpenForm, run

TextFile = Annotated[str, FileHint(extensions=(".txt", ".md"))]

Keyword = Annotated[str, Min(1), Max(20), Label("Keyword")]


def analyse_document(document: TextFile, keyword: Keyword = "the") -> str:
    """Count how often a keyword appears in a stored document."""
    words = Path(document).read_text(encoding="utf-8").split()
    matches = sum(1 for word in words if word.lower() == keyword.lower())

    return f"{matches} matches for {keyword!r} in {len(words)} words"


def choose_document(
    document: TextFile,
) -> Annotated[dict, OpenForm(analyse_document)]:
    """Upload a document once and land on the analysis form with it in place.

    The returned document travels as a prefill value, and a prefilled file is
    treated as an existing file rather than as a new choice: before the page
    is served the path has to belong to the storage directory and to carry an
    extension the field accepts, and what the plan publishes is the reference,
    never the path. Nothing opens it — a prefilled file is neither read nor
    weighed, because only the file picked in the browser has bytes to
    measure. The widget shows it as the current file, and submitting sends
    its reference without uploading a single byte again.
    """
    return {"document": document}


if __name__ == "__main__":
    run([choose_document, analyse_document], title="File prefill")
