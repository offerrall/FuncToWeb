from typing import Annotated
from pydantic import Field
from PIL import Image
from func_to_web import run
from func_to_web.types import ImageFile, FileResponse
from io import BytesIO

def resize(
    photo: ImageFile,
    width:  Annotated[int, Field(ge=10, le=4000)] = 800,
    height: Annotated[int, Field(ge=10, le=4000)] = 600,
):
    img = Image.open(photo).resize((width, height))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return FileResponse(data=buf.getvalue(), filename="resized.png")

run(resize)
