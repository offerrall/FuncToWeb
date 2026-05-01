from func_to_web import run
from func_to_web.types import ImageFile, FileResponse
from PIL import Image, ImageFilter
import matplotlib.pyplot as plt

def analyze(photo: ImageFile):
    img = Image.open(photo)
    blurred = img.filter(ImageFilter.GaussianBlur(5))

    fig, ax = plt.subplots()
    pixels = [p for px in img.getdata() for p in (px if isinstance(px, tuple) else (px,))]
    ax.hist(pixels, bins=50)
    ax.set_title("Pixel distribution")

    info = f"Size: {img.size}, Mode: {img.mode}"
    report = FileResponse(data=info.encode(), filename="info.txt")

    return (info, blurred, fig, report)

run(analyze)
