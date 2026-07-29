# Table with numpy

Optional dependency: **numpy**.

```bash
pip install numpy
```

`matrix.py` builds an operation table using broadcasting and returns the
two-dimensional `numpy.ndarray`, which is converted into a `table` output.

What it demonstrates:

* a numpy array becomes a table only if it has exactly two dimensions: a 1D or
  a 3D array does not, and would end up as text;
* since there are no column names, the headers are generated: `Column 1`,
  `Column 2`, …;
* every cell is converted with `str()`, so a `numpy.int64` is serialized like
  any other value, regardless of its type.

Run it from the repository root:

```bash
python examples/outputs_optional/numpy/matrix.py
```
