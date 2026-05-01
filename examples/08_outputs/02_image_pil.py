from func_to_web import run
from func_to_web.types import ImageFile
from PIL import Image, ImageFilter

def blur(photo: ImageFile, radius: int = 5):
    return Image.open(photo).filter(ImageFilter.GaussianBlur(radius))

run(blur)
