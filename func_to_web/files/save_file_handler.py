import asyncio
import uuid
from pathlib import Path
from typing import Any

CHUNK_SIZE = 8 * 1024 * 1024


async def save_uploaded_file(
    uploaded_file: Any,
    uploads_dir: Path,
    max_file_size: int | None = None,
) -> str:
    """Save uploaded file with optional size limit."""
    original_name = getattr(uploaded_file, 'filename', None) or 'file'
    if not original_name.strip():
        original_name = 'file'
    # Sanitize: strip any directory components (e.g. "../../../etc/passwd")
    # to prevent path traversal attacks. Also reject bare "." and "..".
    sanitized = Path(original_name).name
    if sanitized in (".", "..") or not sanitized.strip():
        sanitized = 'file'
    original_name = sanitized

    folder_path = uploads_dir / uuid.uuid4().hex
    folder_path.mkdir(parents=True, exist_ok=True)
    file_path = folder_path / original_name

    bytes_written = 0

    try:
        with open(file_path, 'wb') as f:
            while chunk := await uploaded_file.read(CHUNK_SIZE):
                bytes_written += len(chunk)

                if max_file_size is not None and bytes_written > max_file_size:
                    raise ValueError(
                        f"File too large: {bytes_written / (1024*1024):.1f} MB "
                        f"(max: {max_file_size / (1024*1024):.1f} MB)"
                    )

                # Offload the blocking write to a thread so the event loop stays
                # responsive (8 MB chunks make the thread-hop overhead negligible).
                await asyncio.to_thread(f.write, chunk)
    except:
        _remove_folder(folder_path)
        raise

    return str(file_path)


def cleanup_uploaded_file(file_path: str) -> None:
    """Delete uploaded file and its UUID folder."""
    _remove_folder(Path(file_path).parent)


def cleanup_uploads_dir(uploads_dir: Path) -> int:
    """Remove all folders in uploads dir. Run once at startup."""
    if not uploads_dir.exists():
        return 0

    count = 0
    for folder in uploads_dir.iterdir():
        if folder.is_dir():
            _remove_folder(folder, root=uploads_dir)
            count += 1

    return count


def _remove_folder(folder_path: Path, root: Path | None = None) -> None:
    """Remove a folder and all its contents.

    `root` is a safety guard: if `folder_path` equals it, nothing is removed
    (prevents deleting the uploads root itself).
    """
    if not folder_path.exists() or folder_path == root:
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
