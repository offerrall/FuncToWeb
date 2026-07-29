from collections.abc import Callable
from typing import Any

from func_to_web.models.return_parser import ReturnContractError
from func_to_web.outputs.download import DownloadOutput, download_output
from func_to_web.outputs.form import FormOutput, form_output
from func_to_web.outputs.image import (
    ImageOutput,
    figure_output,
    image_output,
    is_figure,
    is_image,
)
from func_to_web.outputs.table import TableOutput, table_output
from func_to_web.outputs.text import TextOutput, text_output

__all__ = [
    "DownloadOutput",
    "FormOutput",
    "ImageOutput",
    "Output",
    "TableOutput",
    "TextOutput",
    "download_output",
    "figure_output",
    "form_output",
    "image_output",
    "output_of",
    "table_output",
    "text_output",
]

Output = TextOutput | ImageOutput | TableOutput | DownloadOutput | FormOutput

COLLECTIONS: tuple[type, ...] = (list, tuple)


def outputs_of(
    value: Any,
    *,
    download: Callable[[Any], DownloadOutput | None] | None = None,
    stack: tuple[Any, ...] = (),
) -> list[Output]:
    table = table_output(value)

    if table is not None:
        return [table]

    if type(value) in COLLECTIONS:
        if not value:
            return [text_output("Done")]

        if any(value is seen for seen in stack):
            raise ReturnContractError("recursive output collection")

        nested = (*stack, value)

        return [output
                for item in value
                for output in outputs_of(item, download=download,
                                         stack=nested)]

    if value is None:
        return [text_output("Done")]

    if download is not None:
        produced = download(value)

        if produced is not None:
            return [produced]

    if is_image(value):
        return [image_output(value)]

    if is_figure(value):
        return [figure_output(value)]

    return [text_output(value if type(value) is str else str(value))]


def output_of(
    value: Any,
    *,
    download: Callable[[Any], DownloadOutput | None] | None = None,
) -> Output | list[Output]:
    outputs = outputs_of(value, download=download)

    if len(outputs) == 1 and not _several(value):
        return outputs[0]

    return outputs


def _several(value: Any) -> bool:
    return type(value) in COLLECTIONS and len(value) > 0
