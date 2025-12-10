# File Uploads

Handle file uploads easily with specialized file types.

<div class="grid" markdown>

<div markdown>

func-to-web provides specialized file types for different use cases:
```python
from func_to_web import run
from func_to_web.types import ImageFile, DataFile, TextFile, DocumentFile, File

def process_files(
    any_file: File,         # any file type
    photo: ImageFile,       # .png, .jpg, .jpeg, .gif, .webp...
    data: DataFile,         # .csv, .xlsx, .xls, .json...
    notes: TextFile,        # .txt, .md, .log...
    report: DocumentFile    # .pdf, .doc, .docx...
):
    return "Files uploaded successfully!"

run(process_files)
```

Each file type automatically validates the file extension and provides appropriate file picker filters in the UI.

All file types are represented as strings (file paths) in your function.

</div>

<div markdown>

![File Upload](images/files.jpg)

</div>

</div>

## Upload Progress & Performance

<div class="grid" markdown>

<div markdown>

When uploading files, you'll see real-time feedback:

- **Progress bar** showing 0-100% completion
- **File size display** (e.g., "Uploading 245 MB of 1.2 GB")

**Performance highlights:**

- **Large file support**: Efficiently handles 1GB to 10GB+ files
- **High speeds**: ~237 MB/s localhost, ~100-115 MB/s on Gigabit Ethernet
- **Low memory footprint**: Constant memory usage regardless of file size

</div>

<div markdown>

![Upload Progress](images/upload.jpg)

</div>

</div>

## Working with Uploaded Files

Uploaded files are saved to temporary locations. You can access them as file paths:
```python
from func_to_web import run
from func_to_web.types import ImageFile
from PIL import Image

def process_image(image: ImageFile):
    # image is a file path (str)
    img = Image.open(image)
    # Process the image...
    return f"Image size: {img.size}"

run(process_image)
```

## File Cleanup for Uploaded Files

**Important:** func-to-web does **not** automatically clean up uploaded files. They are saved to the system's temporary directory:

- **Linux/Mac**: `/tmp`
- **Windows**: `%TEMP%` (typically `C:\Users\Username\AppData\Local\Temp`)

### OS Cleanup Behavior

| OS | Automatic Cleanup | When |
|----|-------------------|------|
| **Linux** | ✅ Yes | On restart (and often after 10 days) |
| **macOS** | ✅ Yes | On restart (and after 3 days unused) |
| **Windows** | ⚠️ Maybe | Only if Storage Sense is enabled (disabled by default) |

**Warning for Windows users:** Files in `%TEMP%` can accumulate indefinitely unless you manually run Disk Cleanup or enable Storage Sense.

### Cleanup Options

**Option 1: Let the OS handle it** (simple, but unreliable on Windows)
```python
def process_image(image: ImageFile):
    img = Image.open(image)
    return img.filter(ImageFilter.BLUR)
    # File remains in temp directory
```

**Option 2: Manual cleanup** (recommended for production)
```python
import os

def process_image(image: ImageFile):
    try:
        img = Image.open(image)
        result = img.filter(ImageFilter.BLUR)
        return result
    finally:
        os.unlink(image)  # Delete file immediately
```

**Option 3: Process in-memory** (for small files)
```python
import os

def process_image(image: ImageFile):
    with open(image, 'rb') as f:
        data = f.read()
    os.unlink(image)  # Delete immediately after reading
    # Process data in memory...
```

**Recommendation:** For production applications, especially on Windows, implement manual cleanup (Option 2) to avoid disk space issues.

### Returned Files (Different Behavior)

Files you **return** using `FileResponse` are handled differently and **are** automatically cleaned up by func-to-web after 24 hours (configurable). See [File Downloads](downloads.md) for details.

## Next Steps

- [Lists](lists.md) - Learn about list inputs
- [Optional Types](optional.md) - Make parameters optional
- [Dropdowns](dropdowns.md) - Use dropdown menus for inputs