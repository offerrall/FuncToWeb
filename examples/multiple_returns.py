from func_to_web import run
from func_to_web.types import FileResponse, ImageFile
from PIL import Image, ImageFilter
import matplotlib.pyplot as plt
import numpy as np


def analyze_image(image: ImageFile, blur_radius: int = 5):
    """Process an image and return multiple outputs at once"""
    
    # 1. Process the image
    img = Image.open(image)
    blurred = img.filter(ImageFilter.GaussianBlur(blur_radius))
    
    # 2. Create a plot
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    ax.plot(x, y)
    ax.set_title('Sample Plot')
    ax.grid(True)
    
    # 3. Create a downloadable file
    report = FileResponse(
        data=f"Image processed with blur radius: {blur_radius}\nSize: {img.size}".encode('utf-8'),
        filename="report.txt"
    )
    
    # 4. Return EVERYTHING at once in a tuple
    return (
        "✓ Analysis complete!",  # Text shown first
        blurred,                  # Processed image
        fig,                      # Plot
        report                    # Download button
    )

run(analyze_image)