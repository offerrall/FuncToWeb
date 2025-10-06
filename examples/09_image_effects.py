from func_to_web import run, ImageFile, Literal
from PIL import Image, ImageFilter, ImageEnhance

def apply_effect(
    image: ImageFile,
    effect: Literal['blur', 'sharpen', 'contour', 'emboss', 'edge_enhance'] = 'blur',
    intensity: float = 1.0
):
    """Apply various effects to images"""
    img = Image.open(image)
    
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