import sys
from base64 import b64encode
from io import BytesIO
from typing import Any, TypedDict

PNG_MODES: frozenset[str] = frozenset({"1", "L", "LA", "I", "P", "RGB", "RGBA"})


class ImageOutput(TypedDict):
    type: str
    value: str


def _png_output(buffer: BytesIO) -> ImageOutput:
    data = b64encode(buffer.getvalue()).decode("ascii")

    return {
        "type": "image",
        "value": f"data:image/png;base64,{data}",
    }


def is_image(value: Any) -> bool:
    module = sys.modules.get("PIL.Image")
    image_type = getattr(module, "Image", None)

    return image_type is not None and isinstance(value, image_type)


def image_output(image: Any) -> ImageOutput:
    if image.mode not in PNG_MODES:
        image = image.convert("RGB")

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return _png_output(buffer)


def is_figure(value: Any) -> bool:
    module = sys.modules.get("matplotlib.figure")
    figure_type = getattr(module, "Figure", None)

    return figure_type is not None and isinstance(value, figure_type)


def figure_output(figure: Any) -> ImageOutput:
    buffer = BytesIO()
    figure.savefig(buffer, format="png", bbox_inches="tight")

    pyplot = sys.modules.get("matplotlib.pyplot")

    if pyplot is not None:
        pyplot.close(figure)

    return _png_output(buffer)
