import shutil
from func_to_web import run
from func_to_web.types import ImageFile

def save_photo(photo: ImageFile):
    target = "/tmp/saved_photo.jpg"
    shutil.move(photo, target)
    return f"Saved to {target}"

run(save_photo)
