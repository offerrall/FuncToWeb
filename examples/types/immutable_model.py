"""An @immutable model validates itself and holds its collections in tuples."""

from typing import Annotated

from func_to_web import Max, Min, immutable, run

Channel = Annotated[float, Min(0.0), Max(1.0)]


@immutable
class Layer:
    """One layer of a document; it cannot change once built."""

    name: Annotated[str, Min(1), Max(30)]
    color: tuple[Channel, Channel, Channel] = (0.0, 0.0, 1.0)
    tags: tuple[str, ...] = ()


def describe_layer(layer: Layer) -> str:
    """Describe a layer given as an immutable model."""
    tags = ", ".join(layer.tags) or "no tags"

    return f"{layer.name}: colour {layer.color}, {tags}"


if __name__ == "__main__":
    run(describe_layer, title="Immutable model")
