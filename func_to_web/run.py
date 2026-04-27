from pathlib import Path
from typing import Any, Callable

from .core import save_file_handler, return_file_handler
from .core.server import create_fastapi_app, start_server
from .core.normalization import normalize_input
from .core.auth import setup_auth
from .core.utils import print_beta_warning, create_pytypeinput_assets

from .models import FunctionMetadata
from .routes import setup_multi_items, setup_single_function, setup_download_route, setup_doc_route
from . import call_function


def run(
    func: Callable[..., Any] | FunctionMetadata | list,
    host: str = "0.0.0.0",
    port: int = 8000,
    auth: dict[str, str] | None = None,
    secret_key: str | None = None,
    app_title: str | None = None,
    css_vars: dict[str, str] | None = None,
    favicon: str | Path | None = None,
    uploads_dir: str | Path = "./uploads",
    max_file_size: int | None = None,
    keep_uploads: bool = False,
    returns_dir: str | Path = "./returned_files",
    returns_lifetime: int = 3600,
    stream_prints: bool = True,
    root_path: str = "",
    fastapi_config: dict[str, Any] | None = None,
    front_dir: str | Path | None = None,
    assets_dir: str | Path | None = None,
    **uvicorn_kwargs
):
    """Run the web application server.

    Args:
        func: Single function, FunctionMetadata, or list of functions/groups.
        host: Server host address.
        port: Server port.
        auth: Optional dictionary of {username: password} for authentication.
        secret_key: Secret key for session signing. Auto-generated if None.
        app_title: Custom application title.
        css_vars: CSS variable overrides.
        favicon: Path to favicon file.
        uploads_dir: Directory for uploaded files.
        max_file_size: Maximum size in bytes for uploaded files, None for unlimited.
        keep_uploads: If True, uploaded files are not deleted after function execution.
        returns_dir: Directory for files returned by functions.
        returns_lifetime: Seconds before returned files are deleted (default: 3600).
        stream_prints: If True, print() output is streamed to the client in real time.
        root_path: FastAPI root path for reverse proxy.
        fastapi_config: Additional FastAPI configuration.
        front_dir: Optional directory served at /front (with html=True for SPA-style routing).
        assets_dir: Optional directory served at /assets.
        **uvicorn_kwargs: Additional Uvicorn configuration.
    """
    print_beta_warning()
    create_pytypeinput_assets()

    save_file_handler.UPLOADS_DIR = Path(uploads_dir)
    save_file_handler.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    save_file_handler.MAX_FILE_SIZE = max_file_size
    save_file_handler.KEEP_UPLOADS = keep_uploads

    return_file_handler.RETURNS_DIR = Path(returns_dir)
    return_file_handler.RETURNS_DIR.mkdir(parents=True, exist_ok=True)
    return_file_handler.RETURNS_LIFETIME_SECONDS = returns_lifetime

    call_function.STREAM_PRINTS = stream_prints

    count = save_file_handler.cleanup_uploads_dir()
    if count > 0:
        print(f"Cleaned up {count} leftover upload folders from previous run")

    count = return_file_handler.cleanup_returned_files()
    if count > 0:
        print(f"Cleaned up {count} expired returned files from previous run")

    return_file_handler.start_cleanup_timer()

    app_input = normalize_input(func, app_title, css_vars, favicon)

    if fastapi_config is None:
        fastapi_config = {}

    app = create_fastapi_app(root_path, fastapi_config, front_dir, assets_dir)

    setup_download_route(app)
    setup_doc_route(app, app_input)

    if app_input.single_function:
        setup_single_function(app, app_input)
    else:
        setup_multi_items(app, app_input)

    if auth:
        setup_auth(app, auth, secret_key)

    start_server(app, host, port, uvicorn_kwargs)