# File Uploads

Handle file uploads easily with specialized file types.

<div class="grid" markdown>

<div markdown>

func-to-web provides specialized file types for different use cases:

```python
from func_to_web import run
from func_to_web.types import ImageFile, DataFile, TextFile, DocumentFile

def process_files(
    photo: ImageFile,       # .png, .jpg, .jpeg, .gif, .webp
    data: DataFile,         # .csv, .xlsx, .xls, .json
    notes: TextFile,        # .txt, .md, .log
    report: DocumentFile    # .pdf, .doc, .docx
):
    return "Files uploaded successfully!"

run(process_files)
```

Each file type automatically validates the file extension and provides appropriate file picker filters in the UI.

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

Uploaded files are saved to the system's temporary directory (`/tmp` on Linux/Mac, `%TEMP%` on Windows) and remain there after processing. Delete them manually if needed, or they'll be cleaned up by the OS eventually (typically on restart).

## Next Steps

- [Lists](lists.md) - Learn about list inputs
- [Optional Types](optional.md) - Make parameters optional
- [Dropdowns](dropdowns.md) - Use dropdown menus for inputs