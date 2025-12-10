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
- **Persistent registry**: Files tracked in SQLite database (thread-safe)
- **1-hour grace period**: Files remain available for 1 hour after download
- **Automatic cleanup**: Old files removed after 24 hours (configurable)

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

- **No size limits**: Uses temporary files and streaming
- **Constant memory usage**: Regardless of file size
- **Same efficiency as file uploads**: 8MB chunks
- **SQLite registry**: Thread-safe file tracking with persistent database
- **Background cleanup**: Non-blocking startup cleanup process

## File Cleanup & Retention

Generated files have a **smart cleanup lifecycle**:

1. **Immediate availability**: Files ready for download right after generation
2. **1-hour grace period**: After first download, files remain available for re-download for 1 hour
3. **24-hour retention**: Files older than 24 hours are automatically cleaned up on server startup
4. **Configurable**: Adjust retention period with `cleanup_hours` parameter
```python
# Default: 24-hour cleanup
run(my_function)

# Custom: 6-hour cleanup
run(my_function, cleanup_hours=6)

# Disable auto-cleanup
run(my_function, cleanup_hours=0)
```

**Database location** is also configurable:
```python
# Default: func_to_web.db in current directory
run(my_function)

# Custom location
run(my_function, db_location="/path/to/data")

# Temporary (uses system temp dir)
import tempfile
run(my_function, db_location=tempfile.gettempdir())
```

## Auto-Healing

If a file is manually deleted from disk but still exists in the database, the system automatically detects this and cleans up the broken reference when someone tries to download it.

## What's Next?

You've completed all **Output Types**! Explore additional features.

**Next category:**

- [Tables](tables.md) - Return tables from lists or DataFrames
- [Multiple Outputs](multiple-outputs.md) - Return multiple outputs from a single function