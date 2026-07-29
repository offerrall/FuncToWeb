# Chart with matplotlib

Optional dependency: **matplotlib**.

```bash
pip install matplotlib
```

`figure.py` plots a sine wave and returns the `matplotlib.figure.Figure`, which
FuncToWeb saves as a PNG with `bbox_inches="tight"` and delivers as an `image`
output.

What it demonstrates:

* the **figure** is recognized, not the `Axes`: returning `axes` would produce
  its `str()` as text;
* the figure is built with `Figure(...)`, without `pyplot`: there is no backend
  to choose, no window opens, and the figure never enters the global `pyplot`
  registry;
* if you use `pyplot`, set a non-interactive backend first with
  `matplotlib.use("Agg")`; FuncToWeb closes the figure with `pyplot.close()`.

Run it from the repository root:

```bash
python examples/outputs_optional/matplotlib/figure.py
```
