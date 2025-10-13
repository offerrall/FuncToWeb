import io
import base64
import tempfile
from .types import FileResponse as UserFileResponse

def process_result(result):
    """
    Convert function result to appropriate display format.
    
    Handles images (PIL, Matplotlib), single/multiple files, and text.
    Returns a dictionary with 'type' and relevant data.
    Files are saved to temporary files and paths are returned.
    """
    # PIL Image detection
    try:
        from PIL import Image
        if isinstance(result, Image.Image):
            buffer = io.BytesIO()
            result.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()
            return {
                'type': 'image',
                'data': f'data:image/png;base64,{img_base64}'
            }
    except ImportError:
        pass
    
    # Matplotlib Figure detection
    try:
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        if isinstance(result, Figure):
            buffer = io.BytesIO()
            result.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(result)
            return {
                'type': 'image',
                'data': f'data:image/png;base64,{img_base64}'
            }
    except ImportError:
        pass
    
    # Single file - save to temp
    if isinstance(result, UserFileResponse):
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{result.filename}") as tmp:
            tmp.write(result.data)
            return {
                'type': 'download',
                'path': tmp.name,
                'filename': result.filename
            }
    
    # Multiple files - save to temp
    if isinstance(result, list) and len(result) > 0 and all(isinstance(f, UserFileResponse) for f in result):
        files = []
        for f in result:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{f.filename}") as tmp:
                tmp.write(f.data)
                files.append({
                    'path': tmp.name,
                    'filename': f.filename
                })
        return {
            'type': 'downloads',
            'files': files
        }
    
    # Default: convert to string
    return {
        'type': 'text',
        'data': str(result)
    }