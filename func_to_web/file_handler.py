import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

from . import config

CHUNK_SIZE = 8 * 1024 * 1024
FILE_BUFFER_SIZE = 8 * 1024 * 1024
MAX_FILENAME_LENGTH = 255
MAX_USER_FILENAME_LENGTH = 100


def _encode_filename(file_id: str, timestamp: int, original_name: str) -> str:
    """Encode file metadata in filename for RETURNED files.
    
    Used only for files returned by user functions (FileResponse).
    Format: {file_id}___{timestamp}___{safe_filename}
    Example: 550e8400-e29b-41d4-a716-446655440000___1702380000___report.pdf
    
    Args:
        file_id: UUID for the file.
        timestamp: Unix timestamp (seconds since epoch).
        original_name: Filename from user's FileResponse.
        
    Returns:
        Encoded filename string.
    """
    safe_name = original_name.replace('/', '_').replace('\\', '_').replace('___', '_')
    return f"{file_id}___{timestamp}___{safe_name}"


def _decode_filename(encoded_name: str) -> dict[str, Any] | None:
    """Decode file metadata from filename for RETURNED files.
    
    Used only for files returned by user functions (FileResponse).
    
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


def _sanitize_filename(filename: str) -> str:
    """Sanitize user-uploaded filename against security attacks.
    
    Used only for UPLOADED files (files received from users).
    Protects against:
    - Directory traversal (../, ../../)
    - Special characters that could cause issues
    - Reserved names on Windows (CON, PRN, AUX, etc.)
    - Unicode homoglyphs
    - Null bytes
    
    Args:
        filename: Original filename from user upload.
        
    Returns:
        Safe filename with only alphanumeric chars, dots, hyphens, underscores, and spaces.
    """
    filename = os.path.basename(filename)
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    safe = re.sub(r'[^a-zA-Z0-9._\s-]', '_', filename)
    safe = re.sub(r'\.{2,}', '.', safe)
    safe = re.sub(r'_{2,}', '_', safe)
    safe = re.sub(r'\s{2,}', ' ', safe)
    safe = safe.strip('. _')
    
    reserved = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    name_without_ext = os.path.splitext(safe)[0].upper()
    if name_without_ext in reserved:
        safe = f"file_{safe}"
    
    if not safe or safe == '.' or safe == '..':
        safe = 'file'
    
    return safe


async def save_uploaded_file(uploaded_file: Any, suffix: str) -> str:
    """Save an UPLOADED file (received from user) to uploads directory.
    
    Sanitizes filename, preserves original name (up to 100 chars), and adds unique ID.
    Format: {sanitized_name}_{unique_id}.{ext}
    Example: My_Report_2024_a3b4c5d6e7f8g9h0i1j2k3l4m5n6o7p8.pdf
    
    Security features:
    - Filename sanitization against directory traversal
    - 100 character limit on user-provided name
    - UUID for uniqueness filename
    - Path resolution check to ensure file stays in uploads directory
    
    Args:
        uploaded_file: The uploaded file object from FastAPI.
        suffix: File extension to use as fallback.
        
    Returns:
        Path to the saved file (string).
        
    Raises:
        ValueError: If security check fails (file would be outside uploads directory).
    """
    original_name = uploaded_file.filename if hasattr(uploaded_file, 'filename') else 'file'
    safe_name = _sanitize_filename(original_name)
    
    name_without_ext, ext = os.path.splitext(safe_name)
    if not ext:
        ext = suffix
    
    if len(name_without_ext) > MAX_USER_FILENAME_LENGTH:
        name_without_ext = name_without_ext[:MAX_USER_FILENAME_LENGTH]
    
    unique_id = uuid.uuid4().hex
    final_name = f"{name_without_ext}_{unique_id}{ext}"
    
    file_path = config.UPLOADS_DIR / final_name
    file_path_resolved = file_path.resolve()
    uploads_dir_resolved = config.UPLOADS_DIR.resolve()
    
    if not str(file_path_resolved).startswith(str(uploads_dir_resolved)):
        raise ValueError("Security: Invalid file path detected")
    
    with open(file_path, 'wb', buffering=FILE_BUFFER_SIZE) as f:
        while chunk := await uploaded_file.read(CHUNK_SIZE):
            f.write(chunk)
    
    return str(file_path)


def cleanup_uploaded_file(file_path: str) -> None:
    """Delete an UPLOADED file from disk.
    
    Args:
        file_path: Path to the uploaded file.
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception:
        pass


def save_returned_file(data: bytes, filename: str) -> tuple[str, str]:
    """Save a RETURNED file (from user's FileResponse) to returns directory.
    
    This is SAFE because WE control the filename (it comes from user's code, not from upload).
    The filename is already validated by Pydantic (max 150 chars) in FileResponse.
    
    Args:
        data: File content bytes.
        filename: Filename from user's FileResponse (already validated).
        
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
    """Get RETURNED file info by file_id.
    
    Searches the returns directory for a file matching the file_id.
    
    Args:
        file_id: Unique identifier for the returned file.
        
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
    """Remove RETURNED file from disk.
    
    Args:
        file_id: Unique identifier for the returned file.
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
    """Get file_ids of RETURNED files older than max_age_seconds.
    
    Parses timestamps from filenames and compares against current time.
    
    Args:
        max_age_seconds: Maximum age in seconds.
        
    Returns:
        List of file_ids (strings) for returned files.
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
    """Get count of RETURNED files in directory.
    
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
    """Remove RETURNED files older than 1 hour (hardcoded).
    
    This runs on startup and every hour while server is running.
    Only affects files in the returns directory (FileResponse outputs).
    Uploaded files are cleaned up immediately after processing if AUTO_DELETE_UPLOADS is True.
    """
    try:
        max_age_seconds = config.RETURNS_LIFETIME_SECONDS
        old_file_ids = get_old_returned_files(max_age_seconds)
        
        for file_id in old_file_ids:
            cleanup_returned_file(file_id, delete_from_disk=True)
            
    except Exception:
        pass


def create_response_with_files(processed: dict[str, Any]) -> dict[str, Any]:
    """Create JSON response with RETURNED file downloads.
    
    Converts file paths to file_ids for the download endpoint.
    Only processes files returned by user functions (FileResponse).
    
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