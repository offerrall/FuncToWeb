from pathlib import Path

# File directories
UPLOADS_DIR = Path("./uploads")
RETURNS_DIR = Path("./returned_files")

# Auto-delete uploaded files after processing
AUTO_DELETE_UPLOADS: bool = True

# Returned files lifetime (1 hour from creation)
RETURNS_LIFETIME_SECONDS: int = 3600