from func_to_web import run, File
import shutil, os

downloads = os.path.expanduser("~/Downloads")

def upload_files(files: list[File]):
    for f in files:
        shutil.move(f, downloads)
    return "Files uploaded successfully!"

run(upload_files)