"""A file reaches the opened form as its reference, with nothing to send."""

from pathlib import Path
from typing import Annotated

from func_to_web import IsPathFile, Min, OpenForm, run

ReportPath = Annotated[str, IsPathFile(extensions=(".txt", ".md"))]


def summarise_report(
    report: ReportPath,
    title: str = "Report",
    lines: Annotated[int, Min(1)] = 5,
) -> str:
    """Summarise a report that is already stored, with no upload pending."""
    content = Path(report).read_text(encoding="utf-8").splitlines()
    head = "\n".join(content[:lines])

    return f"{title}: {len(content)} lines\n\n{head}"


def choose_report(
    report: ReportPath,
) -> Annotated[dict, OpenForm(summarise_report)]:
    """Hand the uploaded report to the summariser, already in place.

    The function hands back the local path it received, and what travels in
    the opening URL is the file's reference; a file written anywhere else has
    none, so the chaining fails instead of publishing where it was. The second
    page shows it as its current file, with nothing left to send.
    """
    return {"report": report, "title": Path(report).stem}


if __name__ == "__main__":
    run([choose_report, summarise_report], title="Reports")
