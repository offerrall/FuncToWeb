import os
import tempfile
import uuid
import threading
from typing import Any

from .db_manager import register_file, get_file_info, delete_file_record, get_old_files

CHUNK_SIZE = 8 * 1024 * 1024
FILE_BUFFER_SIZE = 8 * 1024 * 1024

_cleanup_locks = {}
_cleanup_locks_lock = threading.Lock()


async def save_uploaded_file(uploaded_file: Any, suffix: str) -> str:
    """Save an uploaded file to a temporary location.
    
    Args:
        uploaded_file: The uploaded file object from FastAPI.
        suffix: File extension to use for the temp file.
        
    Returns:
        Path to the saved temporary file.
    """
    with tempfile.NamedTemporaryFile(
        delete=False, 
        suffix=suffix, 
        buffering=FILE_BUFFER_SIZE
    ) as tmp:
        while chunk := await uploaded_file.read(CHUNK_SIZE):
            tmp.write(chunk)
        return tmp.name


def register_temp_file(file_id: str, path: str, filename: str) -> None:
    """Register a temp file for download.
    
    Args:
        file_id: Unique identifier for the file.
        path: File system path to the temporary file.
        filename: Original filename for download.
    """
    register_file(file_id, path, filename)


def get_temp_file(file_id: str) -> dict[str, str] | None:
    """Get temp file info from registry.
    
    Args:
        file_id: Unique identifier for the file.
        
    Returns:
        Dictionary with 'path' and 'filename' keys, or None if not found.
    """
    return get_file_info(file_id)


def cleanup_temp_file(file_id: str, delete_from_disk: bool = True) -> None:
    """Remove temp file and its registry entry (thread-safe).
    
    Uses threading locks to prevent race conditions when multiple threads
    attempt to clean up the same file simultaneously.
    
    Args:
        file_id: Unique identifier for the file.
        delete_from_disk: If True, delete the physical file from disk.
    """
    with _cleanup_locks_lock:
        if file_id not in _cleanup_locks:
            _cleanup_locks[file_id] = threading.Lock()
        file_lock = _cleanup_locks[file_id]
    
    with file_lock:
        try:
            if delete_from_disk:
                info = get_file_info(file_id)
                if info:
                    try:
                        if os.path.exists(info['path']):
                            os.unlink(info['path'])
                    except FileNotFoundError:
                        pass
                    except Exception:
                        pass
            
            delete_file_record(file_id)
            
        except Exception:
            pass
        finally:
            with _cleanup_locks_lock:
                _cleanup_locks.pop(file_id, None)


def cleanup_old_files(max_age_hours: int = 24) -> None:
    """Remove files older than max_age_hours from database and disk.
    
    Args:
        max_age_hours: Maximum age in hours.
    """
    try:
        old_files = get_old_files(max_age_hours)
        
        for file_data in old_files:
            file_id = file_data['id']
            path = file_data['path']
            
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except Exception:
                pass
            
            delete_file_record(file_id)
            
    except Exception:
        pass


def create_response_with_files(processed: dict[str, Any]) -> dict[str, Any]:
    """Create JSON response with file downloads.
    
    Args:
        processed: Processed result from process_result().
        
    Returns:
        Response dictionary with file IDs and metadata.
    """
    response = {"success": True, "result_type": processed['type']}
    
    if processed['type'] == 'download':
        file_id = str(uuid.uuid4())
        register_temp_file(file_id, processed['path'], processed['filename'])
        response['file_id'] = file_id
        response['filename'] = processed['filename']
    
    elif processed['type'] == 'downloads':
        files = []
        for f in processed['files']:
            file_id = str(uuid.uuid4())
            register_temp_file(file_id, f['path'], f['filename'])
            files.append({
                'file_id': file_id,
                'filename': f['filename']
            })
        response['files'] = files
    
    elif processed['type'] == 'multiple':
        outputs = []
        for output in processed['outputs']:
            output_response = create_response_with_files(output)
            output_response.pop('success', None)
            outputs.append(output_response)
        response['outputs'] = outputs
    
    elif processed['type'] == 'table':
        response['headers'] = processed['headers']
        response['rows'] = processed['rows']
    
    else:
        response['result'] = processed['data']
    
    return response