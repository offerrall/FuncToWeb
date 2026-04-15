import uuid
from pathlib import Path
from typing import Any

import aiofiles

CHUNK_SIZE = 8 * 1024 * 1024

UPLOADS_DIR = Path("./uploads")
MAX_FILE_SIZE: int | None = None
KEEP_UPLOADS: bool = False


async def save_uploaded_file(uploaded_file: Any) -> str:
    """Save uploaded file with optional size limit."""
    original_name = getattr(uploaded_file, 'filename', None) or 'file'
    if not original_name.strip():
        original_name = 'file'

    folder_path = UPLOADS_DIR / uuid.uuid4().hex
    folder_path.mkdir(parents=True, exist_ok=True)
    file_path = folder_path / original_name

    bytes_written = 0

    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await uploaded_file.read(CHUNK_SIZE):
                bytes_written += len(chunk)

                if MAX_FILE_SIZE is not None and bytes_written > MAX_FILE_SIZE:
                    raise ValueError(
                        f"File too large: {bytes_written / (1024*1024):.1f} MB "
                        f"(max: {MAX_FILE_SIZE / (1024*1024):.1f} MB)"
                    )

                await f.write(chunk)
    except:
        _remove_folder(folder_path)
        raise

    return str(file_path)


def cleanup_uploaded_file(file_path: str, force: bool = False) -> None:
    """Delete uploaded file and its UUID folder.
    Skips if keep_uploads is enabled unless force is True (error cleanup)."""
    if KEEP_UPLOADS and not force:
        return

    _remove_folder(Path(file_path).parent)


def cleanup_uploads_dir() -> int:
    """Remove all folders in uploads dir. Run once at startup.
    Skips if keep_uploads is enabled."""
    if KEEP_UPLOADS or not UPLOADS_DIR.exists():
        return 0

    count = 0
    for folder in UPLOADS_DIR.iterdir():
        if folder.is_dir():
            _remove_folder(folder)
            count += 1

    return count


def _remove_folder(folder_path: Path) -> None:
    """Remove a folder and all its contents."""
    if not folder_path.exists() or folder_path == UPLOADS_DIR:
        return

    try:
        for item in folder_path.iterdir():
            try:
                item.unlink()
            except OSError:
                pass
        folder_path.rmdir()
    except OSError:
        pass