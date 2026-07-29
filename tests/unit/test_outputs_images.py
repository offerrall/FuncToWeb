import sys
from base64 import b64decode
from io import BytesIO

import pytest

from func_to_web.outputs import figure_output, image_output, output_of
from func_to_web.outputs.image import is_figure, is_image

PREFIX = "data:image/png;base64,"
SIGNATURE = b"\x89PNG\r\n\x1a\n"

PILLOW_I_MODE = "ignore:Saving I mode images as PNG:DeprecationWarning"


class FakeImage:
    mode = "RGB"

    def save(self, buffer, format=None):
        buffer.write(SIGNATURE)


class FakeFigure:
    def savefig(self, buffer, format=None, bbox_inches=None):
        buffer.write(SIGNATURE)


def pil_module():
    return pytest.importorskip("PIL.Image")


def figure_module():
    return pytest.importorskip("matplotlib.figure")


def pyplot_module():
    return pytest.importorskip("matplotlib.pyplot")


def decoded(output):
    return b64decode(output["value"][len(PREFIX):], validate=True)


@pytest.mark.filterwarnings(PILLOW_I_MODE)
@pytest.mark.parametrize("mode", ["1", "L", "LA", "I", "P", "RGB", "RGBA"])
def test_supported_modes_produce_a_valid_png(mode):
    pil = pil_module()
    output = image_output(pil.new(mode, (3, 2)))

    assert output["type"] == "image"
    assert output["value"].startswith(PREFIX)
    assert decoded(output).startswith(SIGNATURE)


@pytest.mark.filterwarnings(PILLOW_I_MODE)
@pytest.mark.parametrize("mode", ["1", "L", "LA", "I", "P", "RGB", "RGBA"])
def test_supported_modes_are_not_converted(mode):
    pil = pil_module()
    image = pil.new(mode, (3, 2))

    image_output(image)

    assert image.mode == mode


def test_unsupported_mode_is_encoded_as_rgb():
    pil = pil_module()
    output = image_output(pil.new("CMYK", (3, 2)))

    with pil.open(BytesIO(decoded(output))) as reopened:
        assert reopened.mode == "RGB"


def test_unsupported_mode_does_not_mutate_the_original():
    pil = pil_module()
    image = pil.new("CMYK", (3, 2))

    image_output(image)

    assert image.mode == "CMYK"


def test_image_keeps_its_size():
    pil = pil_module()
    output = image_output(pil.new("RGB", (7, 4)))

    with pil.open(BytesIO(decoded(output))) as reopened:
        assert reopened.size == (7, 4)


def test_data_uri_carries_the_png_prefix():
    pil = pil_module()

    assert image_output(pil.new("RGB", (1, 1)))["value"].startswith(PREFIX)


def test_data_uri_payload_is_strict_base64():
    pil = pil_module()

    assert decoded(image_output(pil.new("RGB", (2, 2))))


def test_image_output_has_only_type_and_value():
    pil = pil_module()

    assert set(image_output(pil.new("RGB", (1, 1)))) == {"type", "value"}


def test_pillow_image_is_detected():
    pil = pil_module()

    assert is_image(pil.new("RGB", (1, 1))) is True


def test_image_lookalike_is_not_detected():
    pil_module()

    assert is_image(FakeImage()) is False


def test_image_lookalike_becomes_text():
    pil_module()

    assert output_of(FakeImage())["type"] == "text"


def test_pillow_image_becomes_an_image_output():
    pil = pil_module()

    assert output_of(pil.new("RGB", (1, 1)))["type"] == "image"


def test_image_is_not_detected_when_pillow_is_not_imported(monkeypatch):
    pil = pil_module()
    image = pil.new("RGB", (1, 1))

    monkeypatch.delitem(sys.modules, "PIL.Image")

    assert is_image(image) is False


def test_image_falls_back_to_text_when_pillow_is_not_imported(monkeypatch):
    pil = pil_module()
    image = pil.new("RGB", (1, 1))

    monkeypatch.delitem(sys.modules, "PIL.Image")

    assert output_of(image)["type"] == "text"


def test_figure_produces_a_valid_png():
    figures = figure_module()
    figure = figures.Figure()
    figure.add_subplot().plot([1, 2], [3, 4])

    output = figure_output(figure)

    assert output["type"] == "image"
    assert output["value"].startswith(PREFIX)
    assert decoded(output).startswith(SIGNATURE)


def test_figure_is_saved_with_a_tight_bounding_box():
    figures = figure_module()
    figure = figures.Figure()
    recorded = {}
    original = figure.savefig

    def spy(*args, **kwargs):
        recorded.update(kwargs)
        return original(*args, **kwargs)

    figure.savefig = spy
    figure_output(figure)

    assert recorded["bbox_inches"] == "tight"
    assert recorded["format"] == "png"


def test_figure_is_closed_when_pyplot_is_loaded():
    pyplot = pyplot_module()
    figure = pyplot.figure()
    number = figure.number

    assert number in pyplot.get_fignums()

    figure_output(figure)

    assert number not in pyplot.get_fignums()


def test_figure_works_when_pyplot_is_not_loaded(monkeypatch):
    figures = figure_module()
    figure = figures.Figure()

    monkeypatch.delitem(sys.modules, "matplotlib.pyplot", raising=False)

    assert decoded(figure_output(figure)).startswith(SIGNATURE)


def test_figure_is_detected():
    figures = figure_module()

    assert is_figure(figures.Figure()) is True


def test_figure_lookalike_is_not_detected():
    figure_module()

    assert is_figure(FakeFigure()) is False


def test_figure_lookalike_becomes_text():
    figure_module()

    assert output_of(FakeFigure())["type"] == "text"


def test_figure_becomes_an_image_output():
    figures = figure_module()

    assert output_of(figures.Figure())["type"] == "image"


def test_axes_is_not_a_figure():
    figures = figure_module()
    axes = figures.Figure().add_subplot()

    assert is_figure(axes) is False
    assert output_of(axes)["type"] == "text"


def test_figure_is_not_detected_when_matplotlib_is_not_imported(monkeypatch):
    figures = figure_module()
    figure = figures.Figure()

    monkeypatch.delitem(sys.modules, "matplotlib.figure")

    assert is_figure(figure) is False


def test_figure_falls_back_to_text_when_matplotlib_is_not_imported(monkeypatch):
    figures = figure_module()
    figure = figures.Figure()

    monkeypatch.delitem(sys.modules, "matplotlib.figure")

    assert output_of(figure)["type"] == "text"


def test_images_inside_a_collection_keep_their_order():
    pil = pil_module()
    outputs = output_of(["before", pil.new("RGB", (1, 1)), "after"])

    assert [output["type"] for output in outputs] == ["text", "image", "text"]
