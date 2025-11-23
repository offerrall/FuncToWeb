# Multiple Outputs

Return multiple outputs at once - combine text, images, plots, and files in a single response.

## Usage

<div class="grid" markdown>

<div markdown>

Return a tuple or list with mixed types:
```python
from func_to_web import run
from func_to_web.types import FileResponse, ImageFile
from PIL import Image, ImageFilter
import matplotlib.pyplot as plt
import numpy as np

def analyze_image(image: ImageFile, blur_radius: int = 5):
    """Process image and return multiple outputs"""
    
    # Process image
    img = Image.open(image)
    blurred = img.filter(ImageFilter.GaussianBlur(blur_radius))
    
    # Create plot
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    ax.plot(x, y)
    ax.set_title('Sample Plot')
    ax.grid(True)
    
    # Create downloadable file
    report = FileResponse(
        data=f"Processed with blur: {blur_radius}".encode('utf-8'),
        filename="report.txt"
    )
    
    # Return everything at once
    return (
        "✓ Analysis complete!",  # Text
        blurred,                  # PIL Image
        fig,                      # Matplotlib plot
        report                    # File download
    )

run(analyze_image)
```

Each output is displayed in its own container, one after another.

</div>

<div markdown>

![Combined Types](images/multiple_combined.jpg)

</div>

</div>

## Supported Output Types

You can combine any of these in a tuple or list:

- **Text**: Plain strings are displayed as formatted text
- **PIL Images**: Automatically rendered inline
- **Matplotlib Figures**: Converted to images and displayed
- **File Downloads**: Show download buttons with filenames
- **Multiple Files**: Lists of `FileResponse` objects

## How It Works

- Return a **tuple** or **list** from your function
- Each item is processed according to its type
- All outputs are displayed sequentially in the UI
- Each output gets its own styled container
- Works with any combination of types

## Limitations

- **No nesting**: Tuples/lists cannot contain other tuples/lists
- **Example**: `return ("text", (img1, img2))` will raise an error
- **Solution**: Flatten to `return ("text", img1, img2)`

## Key Points

- **Flexible**: Mix text, images, plots, and files freely
- **Simple syntax**: Just return a tuple or list
- **Clean UI**: Each output in its own styled box
- **No configuration**: Works automatically with existing types

## What's Next?

You've completed all **Output Types**! Explore additional features.

**Next category:**

- [Function Descriptions](function-descriptions.md) - Display docstrings in the UI
- [Multiple Functions](multiple.md) - Serve multiple functions at once
- [Dark Mode](dark-mode.md) - Automatic theme switching
- [Server Configuration](server-configuration.md) - Customize server settings