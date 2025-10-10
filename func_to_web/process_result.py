import io
import base64

def process_result(result):
    """
    Convert function result to appropriate display format.
    
    Detects PIL Images and matplotlib Figures and converts them to base64.
    All other types are converted to strings.
    
    Args:
        result: The function's return value
        
    Returns:
        dict: {'type': 'image'|'text', 'data': str}
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
    
    # Default: convert to string
    return {
        'type': 'text',
        'data': str(result)
    }