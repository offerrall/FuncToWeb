import os
import shutil
from func_to_web import run
from func_to_web.types import File

DOWNLOADS = os.path.expanduser("~/Downloads")

def upload_files(files: list[File]):
    for f in files:
        shutil.move(f, DOWNLOADS)
    return f"Moved {len(files)} file(s) to {DOWNLOADS}"

run(upload_files)
