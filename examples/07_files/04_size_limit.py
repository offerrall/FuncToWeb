from func_to_web import run
from func_to_web.types import File

def upload(file: File):
    return f"Got: {file}"

# 10 MB limit
run(upload, max_file_size=10 * 1024 * 1024)
