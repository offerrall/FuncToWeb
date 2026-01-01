# File Downloads

Return files from your functions and users get automatic download buttons.

## Basic Usage

<div class="grid" markdown>

<div markdown>

Return `FileResponse` for single or multiple files:
```python
from func_to_web import run
from func_to_web.types import FileResponse

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

run(create_multiple_files)
```

</div>

<div markdown>

![File Downloads](images/return_files.jpg)

</div>

</div>

## Key Features

- **Single file**: `FileResponse(data=bytes, filename="file.ext")` or `FileResponse(path="/path/to/file", filename="file.ext")`
- **Multiple files**: Return `[FileResponse(...), FileResponse(...)]`
- **Any file type**: PDF, Excel, ZIP, images, JSON, CSV, binary data, etc.
- **Large files**: Uses streaming - handles GB+ files efficiently
- **Clean UI**: List of files with individual download buttons
- **1-hour retention**: Files automatically deleted 1 hour after creation
- **Automatic cleanup**: Runs on startup and every hour

## Working with Libraries

Works with any library that generates files:
```python
from func_to_web import run
from func_to_web.types import FileResponse
import io

# PDF generation
from reportlab.pdfgen import canvas

def create_pdf(title: str):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 750, title)
    pdf.save()
    return FileResponse(data=buffer.getvalue(), filename="document.pdf")

# Excel generation
import pandas as pd

def create_excel(rows: int):
    df = pd.DataFrame({'A': range(rows), 'B': range(rows)})
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    return FileResponse(data=buffer.getvalue(), filename="data.xlsx")

# ZIP files
import zipfile

def create_archive(file_count: int):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        for i in range(file_count):
            zf.writestr(f'file{i}.txt', f'Content {i}')
    return FileResponse(data=buffer.getvalue(), filename="archive.zip")

run([create_pdf, create_excel, create_archive])
```

## Using Existing Files

Return files that already exist on disk (useful for large files or external tools):
```python
from func_to_web import run
from func_to_web.types import FileResponse
import subprocess

# Video processing with ffmpeg
def compress_video(input_video: str) -> FileResponse:
    output = "/tmp/compressed.mp4"
    subprocess.run(['ffmpeg', '-i', input_video, '-vcodec', 'h264', output])
    return FileResponse(path=output, filename="compressed.mp4")

# Database backup
def backup_database() -> FileResponse:
    output = "/tmp/backup.sql"
    subprocess.run(['pg_dump', 'mydb', '-f', output])
    return FileResponse(path=output, filename="backup.sql")

run([compress_video, backup_database])
```

**Note:** When using `path=`, the file is read and copied to the returns directory. The original file remains untouched.

## Performance

- **No size limits**: Handles very large files (GB+) in streaming mode
- **Memory efficient**: Use `path=` for large files, `data=` for small files
- **8MB chunks**: Same efficiency as file uploads
- **Filesystem-based**: Metadata encoded in filenames (no database)
- **Background cleanup**: Non-blocking startup process

## Directory Configuration
```python
# Default directory
run(my_function)
# Returned files stored in: ./returned_files

# Custom directory
run(my_function, returns_dir="/path/to/returns")
```

## Auto-Healing

If a file is manually deleted from disk, the system automatically detects this when someone tries to download it and returns a "File expired" error.

## What's Next?

You've completed all **Output Types**! Explore additional features.

**Next category:**

- [Tables](tables.md) - Return tables from lists or DataFrames
- [Multiple Outputs](multiple-outputs.md) - Return multiple outputs from a single function