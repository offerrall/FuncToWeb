from func_to_web import run
from func_to_web.types import ImageFile

def gallery(photos: list[ImageFile]):
    return f"Got {len(photos)} photos"

run(gallery)
