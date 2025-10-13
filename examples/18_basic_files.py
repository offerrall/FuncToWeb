from func_to_web import run
from func_to_web.types import FileResponse

def create_text_file(content: str):
    data = content.encode('utf-8')
    return FileResponse(data=data, filename="ttutut.txt")

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

run([create_text_file, create_multiple_files])