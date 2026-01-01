import io
import base64
from .types import FileResponse as UserFileResponse
from .file_handler import save_returned_file
from .check_return_is_table import detect_and_convert_table, is_homogeneous_list_of_dicts, is_homogeneous_list_of_tuples


def _process_file_response(file_response: UserFileResponse) -> tuple[str, str]:
    """Process a single FileResponse and return (file_id, file_path).
    
    Args:
        file_response: FileResponse instance with either data or path.
        
    Returns:
        Tuple of (file_id, file_path) for the saved file.
        
    Raises:
        ValueError: If file cannot be read or FileResponse is invalid.
    """

    if file_response.path is not None:
        try:
            with open(file_response.path, 'rb') as file:
                file_data = file.read()
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_response.path}")
        except PermissionError:
            raise ValueError(f"Permission denied reading file: {file_response.path}")
        except Exception as e:
            raise ValueError(f"Error reading file {file_response.path}: {str(e)}")
        
        return save_returned_file(file_data, file_response.filename)
    
    return save_returned_file(file_response.data, file_response.filename)


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

    # ===== TABLE DETECTION =====
    table_result = detect_and_convert_table(result)
    if table_result is not None:
        return table_result
    
    # ===== TUPLE/LIST HANDLING =====
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
                file_id, file_path = _process_file_response(f)
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
        file_id, file_path = _process_file_response(result)
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