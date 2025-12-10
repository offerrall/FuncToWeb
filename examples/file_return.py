from func_to_web import run
from func_to_web.types import FileResponse
import os


LARGE_FILE_DATA = os.urandom(1024 * 1024 * 1024)  # 1GB


def create_text_file(content: str):
    data = content.encode('utf-8')
    return FileResponse(data=data, filename="aa.txt")

def create_large_file(filename: str = "large_file.bin"):
    return FileResponse(data=LARGE_FILE_DATA, filename=filename)

def create_multiple_files(name: str):
    file1 = FileResponse(
        data=f"Hello {name}!".encode('utf-8'),
        filename="hello.txt"
    )
    file2 = FileResponse(
        data=f"Goodbye {name}!".encode('utf-8'),
        filename="goodbye.txt"
    )
    return [file1, file2]

def create_mixed_sizes(prefix: str):
    small = FileResponse(
        data=f"Small file for {prefix}".encode('utf-8'),
        filename=f"{prefix}_small.txt"
    )
    medium = FileResponse(
        data=os.urandom(10 * 1024 * 1024),  # 10MB
        filename=f"{prefix}_medium.bin"
    )
    large = FileResponse(
        data=LARGE_FILE_DATA,
        filename=f"{prefix}_large.bin"
    )
    return [small, medium, large]

# Note: All files are deleted after one hour

run([create_text_file, create_large_file, create_multiple_files, create_mixed_sizes])