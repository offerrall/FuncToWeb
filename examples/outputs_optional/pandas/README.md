# Table with pandas

Optional dependency: **pandas**.

```bash
pip install pandas
```

`dataframe.py` builds a sales report in memory and returns the
`pandas.DataFrame`, which is converted into a `table` output with the column
names as headers.

What it demonstrates:

* a `DataFrame` is a table; a plain `list` or `dict` is not, and would be
  displayed with `str()`;
* the headers are the column names, and every cell goes through `str()`;
* the rows are read with `itertuples()`, which preserves the type of each
  column: an `int64` next to a `float64` is not promoted, and `86` does not
  come out as `86.0`.

Run it from the repository root:

```bash
python examples/outputs_optional/pandas/dataframe.py
```
