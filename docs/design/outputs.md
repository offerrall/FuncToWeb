# Outputs

Why three of the output rules are the way they are. What each output type is,
and what the `Download` contract requires, is in [outputs.md](../outputs.md).

## Why the rows are read with `itertuples()`

With `values.tolist()` an `int64` column next to a `float64` one would be
promoted, and a `1200` would be shown as `1200.0`. Reading with `itertuples()`
preserves the type of each column, so the `str()` that every cell goes through
sees the value the frame really holds.

## Why the figure is closed

A `matplotlib.figure.Figure` is closed with `pyplot.close()` if `pyplot` is
loaded. That is what takes it out of the global figure registry, which would
otherwise grow by one per execution. A `Figure` built without `pyplot` never
enters that registry.

## Why a union cannot mix a download with an ordinary branch

Nothing in the return value says which branch it came from, so a legitimate
`str` from the ordinary branch would be stored as a file. For the same reason
`Annotated[list[Path | None], Download()]` is rejected: `None` can replace a
whole `Download` output, but it cannot stand for one of its inner files.
