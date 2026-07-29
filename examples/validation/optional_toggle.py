"""OptionalToggle decides whether an X | None field starts on or off."""

from typing import Annotated

from func_to_web import Label, Max, Min, OptionalToggle, run


def export_report(
    project: Annotated[str, Min(1), Max(40)],
    row_limit: Annotated[
        int | None,
        Min(1),
        Max(10000),
        OptionalToggle(True),
        Label("Row limit"),
    ] = None,
    note: Annotated[
        str | None,
        Max(200),
        OptionalToggle(False),
        Label("Internal note"),
    ] = None,
) -> str:
    """Export a report with two optional settings.

    An X | None parameter gets a switch that decides whether the value travels
    at all. Without OptionalToggle the switch copies the default, so both here
    would start off; the atom sets that initial position on its own.
    """
    limit = "all rows" if row_limit is None else f"{row_limit} rows"
    tail = "" if note is None else f" ({note})"

    return f"{project}: {limit}{tail}"


if __name__ == "__main__":
    run(export_report, title="Optional switches")
