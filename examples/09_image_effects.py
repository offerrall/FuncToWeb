from PIL import Image, ImageEnhance, ImageFilter

from func_to_web import ImageFile, Literal, run


def apply_effect(
    image: ImageFile,
    effect: Literal['blur', 'sharpen', 'contour', 'emboss', 'edge_enhance'] = 'blur',
    intensity: float | None = None,
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

run(apply_effect)