"""A Pillow image is returned as it is and shown as an image output."""

from typing import Annotated

from PIL import Image, ImageDraw

from func_to_web import Choices, Color, Max, Min, run


def gradient_badge(
    size: Annotated[int, Choices(values=(64, 128, 256, 512))] = 256,
    tint: Color = "#3b82f6",
    label: Annotated[str, Min(1), Max(12)] = "PNG",
) -> Image.Image:
    """Draw a square gradient badge and return it as a Pillow image."""
    red = int(tint[1:3], 16)
    green = int(tint[3:5], 16)
    blue = int(tint[5:7], 16)

    image = Image.new("RGB", (size, size))
    pixels = image.load()

    for y in range(size):
        weight = y / (size - 1)

        for x in range(size):
            shade = (x / (size - 1) + weight) / 2
            pixels[x, y] = (
                int(red * shade),
                int(green * shade),
                int(blue * shade),
            )

    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, size - 9, size - 9), outline="white", width=3)
    draw.text((16, 16), label, fill="white")

    return image


if __name__ == "__main__":
    run(gradient_badge, title="Pillow image")
