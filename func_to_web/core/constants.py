from pathlib import Path
import tempfile

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
INTERNAL_STATIC_DIR = BASE_DIR / "internal_static"

CACHE_DIR = Path(tempfile.gettempdir()) / "func_to_web"
STATIC_DIR = CACHE_DIR / "static"

UVICORN_DEFAULTS = {
    "reload": False,
    "limit_concurrency": 100,
    "limit_max_requests": 1000,
    "timeout_keep_alive": 30,
}