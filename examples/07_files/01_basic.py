from func_to_web import run
from func_to_web.types import File, ImageFile

def upload(document: File, photo: ImageFile):
    return f"Got: {document}, {photo}"

run(upload)
