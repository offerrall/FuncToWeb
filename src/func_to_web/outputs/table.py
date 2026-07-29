import sys
from typing import Any, TypedDict


class TableOutput(TypedDict):
    type: str
    headers: list[str]
    rows: list[list[str]]


def _table(headers: list[str], rows: list[list[Any]]) -> TableOutput:
    return {
        "type": "table",
        "headers": [str(header) for header in headers],
        "rows": [[str(cell) for cell in row] for row in rows],
    }


def _numbered(count: int) -> list[str]:
    return [f"Column {index + 1}" for index in range(count)]


def _is_instance_of(value: Any, module_name: str, attribute: str) -> bool:
    module = sys.modules.get(module_name)
    declared = getattr(module, attribute, None)

    return declared is not None and isinstance(value, declared)


def table_output(value: Any) -> TableOutput | None:
    if _is_instance_of(value, "pandas", "DataFrame"):
        rows = [list(row) for row in value.itertuples(index=False)]

        return _table(value.columns.tolist(), rows)

    if _is_instance_of(value, "polars", "DataFrame"):
        return _table(value.columns, [list(row) for row in value.rows()])

    if _is_instance_of(value, "numpy", "ndarray") and value.ndim == 2:
        return _table(_numbered(value.shape[1]), value.tolist())

    return None
