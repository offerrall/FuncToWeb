from func_to_web import run
from func_to_web.types import File

def upload_files(
    files: list[File],
): 
    for f in files:
        print(f"Uploaded file: {f}")
    return "Files uploaded successfully!"

run(upload_files, auto_delete_uploads=False)