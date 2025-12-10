import os
import time
import uuid
from pathlib import Path
from typing import Any

from . import config

CHUNK_SIZE = 8 * 1024 * 1024
FILE_BUFFER_SIZE = 8 * 1024 * 1024


def _encode_filename(file_id: str, timestamp: int, original_name: str) -> str:
    """Encode file metadata in filename.
    
    Format: {file_id}___{timestamp}___{safe_filename}
    Example: 550e8400-e29b-41d4-a716-446655440000___1702380000___report.pdf
    
    Args:
        file_id: UUID for the file.
        timestamp: Unix timestamp (seconds since epoch).
        original_name: Original filename from user.
        
    Returns:
        Encoded filename string.
    """
    safe_name = original_name.replace('/', '_').replace('\\', '_').replace('___', '_')
    return f"{file_id}___{timestamp}___{safe_name}"


def _decode_filename(encoded_name: str) -> dict[str, Any] | None:
    """Decode file metadata from filename.
    
    Args:
        encoded_name: Filename in format {file_id}___{timestamp}___{filename}
        
    Returns:
        Dictionary with 'file_id', 'timestamp', 'filename' keys, or None if invalid.
    """
    try:
        parts = encoded_name.split("___")
        if len(parts) != 3:
            return None
        
        return {
            'file_id': parts[0],
            'timestamp': int(parts[1]),
            'filename': parts[2]
        }
    except Exception:
        return None


async def save_uploaded_file(uploaded_file: Any, suffix: str) -> str:
    """Save an uploaded file to uploads directory.
    
    Args:
        uploaded_file: The uploaded file object from FastAPI.
        suffix: File extension to use.
        
    Returns:
        Path to the saved file (string).
    """
    file_id = uuid.uuid4().hex[:12]
    file_path = config.UPLOADS_DIR / f"upload_{file_id}{suffix}"
    
    with open(file_path, 'wb', buffering=FILE_BUFFER_SIZE) as f:
        while chunk := await uploaded_file.read(CHUNK_SIZE):
            f.write(chunk)
    
    return str(file_path)


def cleanup_uploaded_file(file_path: str) -> None:
    """Delete an uploaded file from disk.
    
    Args:
        file_path: Path to the uploaded file.
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        pass


def save_returned_file(data: bytes, filename: str) -> tuple[str, str]:
    """Save a returned file to returns directory with metadata in filename.
    
    Args:
        data: File content bytes.
        filename: Original filename.
        
    Returns:
        Tuple of (file_id, file_path).
    """
    file_id = uuid.uuid4().hex
    timestamp = int(time.time())
    encoded_name = _encode_filename(file_id, timestamp, filename)
    file_path = config.RETURNS_DIR / encoded_name
    
    with open(file_path, 'wb') as f:
        f.write(data)
    
    return file_id, str(file_path)


def get_returned_file(file_id: str) -> dict[str, str] | None:
    """Get returned file info by file_id.
    
    Searches the returns directory for a file matching the file_id.
    
    Args:
        file_id: Unique identifier for the file.
        
    Returns:
        Dictionary with 'path' and 'filename' keys, or None if not found.
    """
    try:
        for file_path in config.RETURNS_DIR.iterdir():
            if file_path.is_file():
                metadata = _decode_filename(file_path.name)
                if metadata and metadata['file_id'] == file_id:
                    return {
                        'path': str(file_path),
                        'filename': metadata['filename']
                    }
        return None
    except Exception:
        return None


def cleanup_returned_file(file_id: str, delete_from_disk: bool = True) -> None:
    """Remove returned file from disk.
    
    Args:
        file_id: Unique identifier for the file.
        delete_from_disk: If True, delete the physical file from disk.
    """
    try:
        if delete_from_disk:
            for file_path in config.RETURNS_DIR.iterdir():
                if file_path.is_file():
                    metadata = _decode_filename(file_path.name)
                    if metadata and metadata['file_id'] == file_id:
                        try:
                            os.unlink(file_path)
                        except FileNotFoundError:
                            pass
                        break
    except Exception:
        pass


def get_old_returned_files(max_age_seconds: int) -> list[str]:
    """Get file_ids of returned files older than max_age_seconds.
    
    Parses timestamps from filenames and compares against current time.
    
    Args:
        max_age_seconds: Maximum age in seconds.
        
    Returns:
        List of file_ids (strings).
    """
    try:
        current_time = int(time.time())
        old_file_ids = []
        
        for file_path in config.RETURNS_DIR.iterdir():
            if file_path.is_file():
                metadata = _decode_filename(file_path.name)
                if metadata:
                    age = current_time - metadata['timestamp']
                    if age > max_age_seconds:
                        old_file_ids.append(metadata['file_id'])
        
        return old_file_ids
    except Exception:
        return []


def get_returned_files_count() -> int:
    """Get count of returned files in directory.
    
    Returns:
        Number of valid returned files.
    """
    try:
        count = 0
        for file_path in config.RETURNS_DIR.iterdir():
            if file_path.is_file():
                metadata = _decode_filename(file_path.name)
                if metadata:
                    count += 1
        return count
    except Exception:
        return 0


def cleanup_old_files() -> None:
    """Remove returned files older than 1 hour (hardcoded).
    
    This runs on startup and every hour while server is running.
    """
    try:
        max_age_seconds = config.RETURNS_LIFETIME_SECONDS
        old_file_ids = get_old_returned_files(max_age_seconds)
        
        for file_id in old_file_ids:
            cleanup_returned_file(file_id, delete_from_disk=True)
            
    except Exception:
        pass


def create_response_with_files(processed: dict[str, Any]) -> dict[str, Any]:
    """Create JSON response with file downloads.
    
    Converts file paths to file_ids for the download endpoint.
    
    Args:
        processed: Processed result from process_result().
        
    Returns:
        Response dictionary with file IDs and metadata.
    """
    response = {"success": True, "result_type": processed['type']}
    
    if processed['type'] == 'download':
        path = processed['path']
        filename = Path(path).name
        metadata = _decode_filename(filename)
        
        if metadata:
            response['file_id'] = metadata['file_id']
            response['filename'] = processed['filename']
        else:
            response['file_id'] = 'unknown'
            response['filename'] = processed['filename']
    
    elif processed['type'] == 'downloads':
        files = []
        for f in processed['files']:
            path = f['path']
            filename_on_disk = Path(path).name
            metadata = _decode_filename(filename_on_disk)
            
            if metadata:
                files.append({
                    'file_id': metadata['file_id'],
                    'filename': f['filename']
                })
            else:
                files.append({
                    'file_id': 'unknown',
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