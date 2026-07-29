# Table with polars

Optional dependency: **polars**.

```bash
pip install polars
```

`dataframe.py` builds an inventory report in memory, adds a computed column,
and returns the `polars.DataFrame`, which is converted into a `table` output.

What it demonstrates:

* polars works just like pandas: FuncToWeb recognizes both without depending on
  or importing either;
* the headers are the column names, and the rows come from `rows()`;
* the optional filter can leave the table empty, and that is still a `table`
  output, just without rows.

Run it from the repository root:

```bash
python examples/outputs_optional/polars/dataframe.py
```
