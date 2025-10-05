from FuncToWeb import run, ImageFile, Field, Annotated
from PIL import Image

def resize_image(
    image: ImageFile,
    width: Annotated[int, Field(ge=1, le=4000)] = 800,
    height: Annotated[int, Field(ge=1, le=4000)] = 600
):
    img = Image.open(image)
    img_resized = img.resize((width, height))
    output_path = image.replace('.', '_resized.')
    img_resized.save(output_path)
    return f"Image resized and saved to {output_path}"

run(resize_image)