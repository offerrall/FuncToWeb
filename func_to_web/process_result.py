import io
import base64
from .types import FileResponse as UserFileResponse
from .file_handler import save_returned_file
from .check_return_is_table import detect_and_convert_table, is_homogeneous_list_of_dicts, is_homogeneous_list_of_tuples

def process_result(result):
    """
    Convert function result to appropriate display format.
    """
    # ===== PANDAS DATAFRAME =====
    try:
        import pandas as pd
        if isinstance(result, pd.DataFrame):
            headers = result.columns.tolist()
            rows = [[str(cell) for cell in row] for row in result.values.tolist()]
            return {
                'type': 'table',
                'headers': headers,
                'rows': rows
            }
    except ImportError:
        pass
    
    # ===== NUMPY 2D ARRAY =====
    try:
        import numpy as np
        if isinstance(result, np.ndarray) and result.ndim == 2:
            headers = [f"Column {i+1}" for i in range(result.shape[1])]
            rows = [[str(cell) for cell in row] for row in result.tolist()]
            return {
                'type': 'table',
                'headers': headers,
                'rows': rows
            }
    except ImportError:
        pass
    
    # ===== POLARS DATAFRAME =====
    try:
        import polars as pl
        if isinstance(result, pl.DataFrame):
            headers = result.columns
            rows = [[str(cell) for cell in row] for row in result.rows()]
            return {
                'type': 'table',
                'headers': headers,
                'rows': rows
            }
    except ImportError:
        pass

    # ===== TABLE DETECTION (FIRST) =====
    table_result = detect_and_convert_table(result)
    if table_result is not None:
        return table_result
    
    # ===== TUPLE/LIST HANDLING (with smart nesting validation) =====
    if isinstance(result, (tuple, list)):
        # Empty tuple/list
        if len(result) == 0:
            return {'type': 'text', 'data': str(result)}
        
        # Check for nested tuples/lists that are NOT valid tables
        for nested_item in result:
            if isinstance(nested_item, (tuple, list)):
                # If it's a valid table, allow it
                if not (is_homogeneous_list_of_dicts(nested_item) or is_homogeneous_list_of_tuples(nested_item)):
                    raise ValueError("Nested tuples/lists are not supported. Please flatten your return structure.")
        
        # Special case: list of FileResponse
        if all(isinstance(f, UserFileResponse) for f in result):
            files = []
            for f in result:
                file_id, file_path = save_returned_file(f.data, f.filename)
                files.append({
                    'path': file_path,
                    'filename': f.filename
                })
            return {
                'type': 'downloads',
                'files': files
            }
        
        # General case: process each item recursively
        outputs = []
        for item in result:
            outputs.append(process_result(item))
        
        return {
            'type': 'multiple',
            'outputs': outputs
        }
    
    # ===== PIL IMAGE =====
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
    
    # ===== MATPLOTLIB FIGURE =====
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
    
    # ===== SINGLE FILE =====
    if isinstance(result, UserFileResponse):
        file_id, file_path = save_returned_file(result.data, result.filename)
        return {
            'type': 'download',
            'path': file_path,
            'filename': result.filename
        }
    
    # ===== DEFAULT: TEXT =====
    return {
        'type': 'text',
        'data': str(result)
    }