import os
import time
import uuid
import threading
from pathlib import Path

RETURNS_DIR = Path("./returned_files")
RETURNS_LIFETIME_SECONDS: int = 3600


def _encode_filename(file_id: str, timestamp: int, filename: str) -> str:
    safe = filename.replace("___", "_")
    return f"{file_id}___{timestamp}___{safe}"


def _decode_filename(name: str) -> dict | None:
    parts = name.split("___")
    if len(parts) != 3:
        return None
    try:
        return {"file_id": parts[0], "timestamp": int(parts[1]), "filename": parts[2]}
    except ValueError:
        return None


def save_returned_file(file_response) -> tuple[str, str]:
    """Save a FileResponse to disk.

    Returns:
        (file_id, file_path)
    """
    if file_response.path is not None:
        data = Path(file_response.path).read_bytes()
    else:
        data = file_response.data

    file_id = uuid.uuid4().hex
    timestamp = int(time.time())
    encoded = _encode_filename(file_id, timestamp, file_response.filename)
    file_path = RETURNS_DIR / encoded

    RETURNS_DIR.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(data)

    return file_id, str(file_path)


def get_returned_file(file_id: str) -> dict | None:
    """Find a returned file by file_id.

    Returns:
        {"path": str, "filename": str} or None if not found.
    """
    if not RETURNS_DIR.exists():
        return None

    for p in RETURNS_DIR.iterdir():
        if not p.is_file():
            continue
        meta = _decode_filename(p.name)
        if meta and meta["file_id"] == file_id:
            return {"path": str(p), "filename": meta["filename"]}

    return None


def cleanup_returned_files() -> int:
    """Delete returned files older than RETURNS_LIFETIME_SECONDS.

    Returns:
        Number of files deleted.
    """
    if not RETURNS_DIR.exists():
        return 0

    now = int(time.time())
    count = 0

    for p in RETURNS_DIR.iterdir():
        if not p.is_file():
            continue
        meta = _decode_filename(p.name)
        if meta and (now - meta["timestamp"]) > RETURNS_LIFETIME_SECONDS:
            try:
                p.unlink()
                count += 1
                print(f"Deleted expired returned file: {p.name}")
            except OSError:
                pass

    return count


def start_cleanup_timer() -> None:
    """Start a background thread that cleans up expired returned files every hour.
    
    Safe to call multiple times — only starts one thread per process.
    The thread is a daemon so it dies automatically when the process exits.
    """
    def _loop():
        while True:
            time.sleep(RETURNS_LIFETIME_SECONDS)
            try:
                cleanup_returned_files()
            except Exception:
                pass

    t = threading.Thread(target=_loop, daemon=True)
    t.start()