# Outputs with optional dependencies

Images and tables. FuncToWeb does not depend on any of these libraries or
import them: it checks whether the module is already loaded, so each
dependency is imported only inside its own example.

| Folder | Dependency | Installation | Output |
| --- | --- | --- | --- |
| `pillow/` | Pillow | `pip install pillow` | `image` |
| `matplotlib/` | matplotlib | `pip install matplotlib` | `image` |
| `pandas/` | pandas | `pip install pandas` | `table` |
| `polars/` | polars | `pip install polars` | `table` |
| `numpy/` | numpy | `pip install numpy` | `table` |

Each folder has its own `README.md` with the details. None of these
libraries is a dependency of FuncToWeb, and none of them appears in
`pyproject.toml`: install only the one for the example you want to run.

The reference for the outputs contract is in [`docs/outputs.md`](../../docs/outputs.md).
