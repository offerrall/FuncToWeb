from FuncToWeb import run, ImageFile
from PIL import Image, ImageFilter

def blur_image(
    image: ImageFile,
    radius: int = 5
):
    img = Image.open(image)
    blurred = img.filter(ImageFilter.GaussianBlur(radius))
    return blurred

run(blur_image)