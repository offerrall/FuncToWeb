"""A matplotlib Figure is an image output, saved and closed by the library."""

from math import sin
from typing import Annotated

from matplotlib.figure import Figure

from func_to_web import Choices, Max, Min, Step, run


def wave_chart(
    frequency: Annotated[float, Min(0.5), Max(8.0), Step(0.5)] = 2.0,
    samples: Annotated[int, Min(20), Max(400)] = 200,
    style: Annotated[str, Choices(values=("line", "bars"))] = "line",
) -> Figure:
    """Plot a sine wave and return the matplotlib figure."""
    xs = [index / samples * 6.283185 for index in range(samples)]
    ys = [sin(x * frequency) for x in xs]

    figure = Figure(figsize=(7, 3.5))
    axes = figure.subplots()

    if style == "bars":
        axes.bar(xs, ys, width=6.283185 / samples, color="#3b82f6")
    else:
        axes.plot(xs, ys, color="#3b82f6", linewidth=2)

    axes.set_title(f"sin(x * {frequency})")
    axes.set_xlabel("x")
    axes.set_ylabel("amplitude")
    axes.grid(True, alpha=0.3)

    return figure


if __name__ == "__main__":
    run(wave_chart, title="Matplotlib figure")
