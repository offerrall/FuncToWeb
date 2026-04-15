def _is_pandas_dataframe(obj) -> bool:
    try:
        import pandas as pd
        return isinstance(obj, pd.DataFrame)
    except ImportError:
        return False


def _is_numpy_2d_array(obj) -> bool:
    try:
        import numpy as np
        return isinstance(obj, np.ndarray) and obj.ndim == 2
    except ImportError:
        return False


def _is_polars_dataframe(obj) -> bool:
    try:
        import polars as pl
        return isinstance(obj, pl.DataFrame)
    except ImportError:
        return False


def _is_list_of_dicts(data) -> bool:
    return (isinstance(data, list) and len(data) > 0
            and all(isinstance(item, dict) for item in data))


def _is_list_of_tuples(data) -> bool:
    return (isinstance(data, list) and len(data) > 0
            and all(isinstance(item, tuple) for item in data))


def _make_table(headers: list[str], rows: list[list]) -> dict:
    return {
        "type": "table",
        "headers": headers,
        "rows": [[str(cell) for cell in row] for row in rows],
    }


def try_process_table(result) -> dict | None:
    """Detect if result is a table format and convert it. Returns None if not a table."""
    if _is_pandas_dataframe(result):
        return _make_table(result.columns.tolist(), result.values.tolist())

    if _is_numpy_2d_array(result):
        headers = [f"Column {i+1}" for i in range(result.shape[1])]
        return _make_table(headers, result.tolist())

    if _is_polars_dataframe(result):
        return _make_table(result.columns, result.rows())

    if _is_list_of_dicts(result):
        headers = list(result[0].keys())
        rows = [[item.get(h, "") for h in headers] for item in result]
        return _make_table(headers, rows)

    if _is_list_of_tuples(result):
        headers = [f"Column {i+1}" for i in range(len(result[0]))]
        return _make_table(headers, [list(t) for t in result])

    return None