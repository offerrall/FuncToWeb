"""Lists: the outer constraints bound the length, the inner ones each item."""

from typing import Annotated

from func_to_web import Description, Label, Max, Min, run


def score_report(
    student: Annotated[str, Min(2), Max(40)],
    scores: Annotated[
        list[Annotated[int, Min(0), Max(100)]],
        Min(1),
        Max(10),
        Label("Scores"),
        Description("Between 1 and 10 values, each from 0 to 100"),
    ],
) -> str:
    """Summarise a list of scores that is validated item by item."""
    average = sum(scores) / len(scores)

    return (
        f"{student}: {len(scores)} score(s), "
        f"min {min(scores)}, max {max(scores)}, average {average:.2f}"
    )


if __name__ == "__main__":
    run(score_report, title="List values")
