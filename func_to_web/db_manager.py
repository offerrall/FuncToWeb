import sqlite3
from pathlib import Path
from typing import Optional

DB_FILENAME = "func_to_web.db"
DB_PATH = Path.cwd() / DB_FILENAME


def set_db_path(root_path: str | Path) -> None:
    """Set the database path.
    
    Args:
        root_path: Directory containing the database or full path to database file.
    """
    global DB_PATH
    path = Path(root_path)
    if path.is_dir():
        DB_PATH = path / DB_FILENAME
    else:
        DB_PATH = path


def get_db_connection():
    """Create a database connection with dict-like row access.
    
    Returns:
        SQLite connection with row factory set.
    """
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database table if it doesn't exist."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                filename TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def register_file(file_id: str, path: str, filename: str) -> None:
    """Register a file in the database.
    
    Args:
        file_id: Unique identifier for the file.
        path: File system path to the file.
        filename: Original filename for download.
    """
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO files (id, path, filename) VALUES (?, ?, ?)",
                (file_id, str(path), filename)
            )
            conn.commit()
    except Exception:
        pass


def get_file_info(file_id: str) -> Optional[dict[str, str]]:
    """Get file info from database.
    
    Args:
        file_id: Unique identifier for the file.
        
    Returns:
        Dictionary with 'path' and 'filename' keys, or None if not found.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT path, filename FROM files WHERE id = ?", 
                (file_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    except Exception:
        return None


def delete_file_record(file_id: str) -> None:
    """Remove file record from database.
    
    Args:
        file_id: Unique identifier for the file.
    """
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
            conn.commit()
    except Exception:
        pass


def get_old_files(max_age_hours: int) -> list[dict]:
    """Get files older than max_age_hours.
    
    Args:
        max_age_hours: Maximum age in hours.
        
    Returns:
        List of dictionaries with 'id' and 'path' keys.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT id, path FROM files WHERE created_at < datetime('now', ? || ' hours')",
                (f'-{max_age_hours}',)
            )
            return [dict(row) for row in cursor.fetchall()]
    except Exception:
        return []


def get_file_count() -> int:
    """Get total number of files in database.
    
    Returns:
        Count of registered files.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM files")
            return cursor.fetchone()[0]
    except Exception:
        return 0