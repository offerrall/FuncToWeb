from PIL import Image, ImageFilter

from func_to_web import Literal, run
from func_to_web.types import ImageFile


def image_effect(
    image: ImageFile,
    effect: Literal['blur', 'sharpen', 'contour', 'emboss', 'edge_enhance'] = 'blur',
    intensity: float | None = 5.0, # | None creates an optional value, defaults to 5.0 (All parameters allowed to be optional and defaults values)
):
    """Apply various effects to images"""
    img = Image.open(image)
    intensity = intensity or 1.0
    
    if effect == 'blur':
        return img.filter(ImageFilter.GaussianBlur(intensity * 5))
    elif effect == 'sharpen':
        return img.filter(ImageFilter.SHARPEN)
    elif effect == 'contour':
        return img.filter(ImageFilter.CONTOUR)
    elif effect == 'emboss':
        return img.filter(ImageFilter.EMBOSS)
    elif effect == 'edge_enhance':
        return img.filter(ImageFilter.EDGE_ENHANCE)

run(image_effect)