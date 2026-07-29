"""Whatever was printed stays visible when the function fails afterwards."""

from typing import Annotated

from func_to_web import Max, Min, run

BROKEN_ROW = 3


def import_rows(rows: Annotated[int, Min(1), Max(10)] = 5) -> str:
    """Read rows one by one and fail on the malformed one."""
    for index in range(1, rows + 1):
        print(f"row {index} read")

        if index == BROKEN_ROW:
            raise ValueError(f"row {index} is malformed")

    return f"{rows} row(s) imported"


if __name__ == "__main__":
    run(import_rows, title="Print then error")
