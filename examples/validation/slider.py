"""Slider draws a bounded number as a track, and Step is its stride."""

from typing import Annotated

from func_to_web import Max, Min, Slider, Step, run


def render_settings(
    quality: Annotated[int, Min(0), Max(100), Step(5), Slider()],
    passes: Annotated[int, Min(1), Max(8), Slider(show_value=False)] = 2,
) -> str:
    """Choose render settings with sliders instead of number boxes.

    Slider needs both Min and Max because a track without ends has nothing to
    draw, and Step sets the stride between reachable positions.
    """
    return f"quality {quality} over {passes} pass(es)"


if __name__ == "__main__":
    run(render_settings, title="Sliders")
