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

- **Single file**: Return `FileResponse(data=bytes, filename="file.ext")`
- **Multiple files**: Return `[FileResponse(...), FileResponse(...)]`
- **Any file type**: PDF, Excel, ZIP, images, JSON, CSV, binary data, etc.
- **Large files**: Uses streaming - handles GB+ files efficiently
- **Clean UI**: List of files with individual download buttons
- **Filesystem tracking**: Metadata encoded in filenames (no database required)
- **1-hour retention**: Files available for 1 hour from creation (hardcoded)
- **Automatic cleanup**: Files older than 1 hour removed every hour

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

## Performance

- **No size limits**: Handles very large files (GB+) in streaming mode
- **Constant memory usage**: Regardless of file size
- **Same efficiency as file uploads**: 8MB chunks
- **Filesystem-based**: Metadata encoded in filenames (no database)
- **Background cleanup**: Non-blocking startup cleanup process

## File Cleanup & Retention

Generated files have a **simple 1-hour lifecycle**:

1. **Immediate availability**: Files ready for download right after generation
2. **1-hour retention**: Files automatically deleted 1 hour after creation (hardcoded, non-configurable)
3. **Automatic cleanup**: Cleanup runs on startup and every hour while server runs
4. **No download tracking**: Files expire based on creation time, not download time

**Directory configuration:**
```python
# Default directories
run(my_function)
# Returned files stored in: ./returned_files

# Custom directory
run(
    my_function,
    returns_dir="/path/to/returns"
)
```

## Auto-Healing

If a file is manually deleted from disk, the system automatically detects this when someone tries to download it and returns a "File expired" error.

## What's Next?

You've completed all **Output Types**! Explore additional features.

**Next category:**

- [Tables](tables.md) - Return tables from lists or DataFrames
- [Multiple Outputs](multiple-outputs.md) - Return multiple outputs from a single function