from PIL import Image, ImageFilter

from func_to_web import Annotated, Field, ImageFile, run


def blur_image(
    image: ImageFile,
    radius: Annotated[int, Field(ge=0, le=50)] = 5
):
    """Apply Gaussian blur to an image"""
    img = Image.open(image)
    return img.filter(ImageFilter.GaussianBlur(radius))

run(blur_image)