"""Main server configuration and run function."""
import asyncio
import warnings
from pathlib import Path
from typing import Callable, Any

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .analyze_function import analyze
from .db_manager import set_db_path, init_db, get_file_count
from .file_handler import cleanup_old_files
from .auth import setup_auth_middleware
from .routes import (
    setup_download_route,
    setup_single_function_routes,
    setup_multiple_function_routes
)

__version__ = "0.9.6"


def run(
    func_or_list: Callable[..., Any] | list[Callable[..., Any]], 
    host: str = "0.0.0.0", 
    port: int = 8000, 
    auth: dict[str, str] | None = None,
    secret_key: str | None = None,
    template_dir: str | Path | None = None,
    root_path: str = "",
    db_location: str | Path | None = None,
    cleanup_hours: int = 24,
    fastapi_config: dict[str, Any] | None = None,
    **kwargs
) -> None:
    """Generate and run a web UI for one or more Python functions.
    
    Single function mode: Creates a form at root (/) for the function.
    Multiple functions mode: Creates an index page with links to individual function forms.
    
    Args:
        func_or_list: A single function or list of functions to wrap.
        host: Server host address (default: "0.0.0.0").
        port: Server port (default: 8000).
        auth: Optional dictionary of {username: password} for authentication.
        secret_key: Secret key for session signing (required if auth is used). 
                    If None, a random one is generated on startup.
        template_dir: Optional custom template directory.
        root_path: Prefix for the API path (useful for reverse proxies).
        db_location: Directory or path for the SQLite database. 
                     If None, uses current working directory.
        cleanup_hours: Auto-cleanup files older than this many hours (default: 24).
                       Set to 0 to disable auto-cleanup.
        fastapi_config: Optional dictionary with extra arguments for FastAPI app 
                        (e.g. {'title': 'My App', 'version': '1.0.0'}).
        **kwargs: Extra options passed directly to `uvicorn.Config`.
                  Examples: `ssl_keyfile`, `ssl_certfile`, `log_level`.
        
    Raises:
        ValueError: If workers > 1 is specified.
        FileNotFoundError: If template directory or database parent directory doesn't exist.
        TypeError: If function parameters use unsupported types.
    """
    
    if kwargs.get('workers', 1) > 1:
        raise ValueError(
            "\n" + "="*70 + "\n"
            "func-to-web does not support multiple workers (workers > 1)\n"
            "="*70 + "\n"
            "Reason: SQLite-based file tracking is not designed for concurrent\n"
            "        writes across multiple processes.\n\n"
            "For scaling:\n"
            "  • Single worker can handle 500-1000 req/s with async I/O\n"
            "  • For higher loads, run multiple instances:\n\n"
            "      # Terminal 1\n"
            "      python app.py --port 8001\n\n"
            "      # Terminal 2\n"
            "      python app.py --port 8002\n\n"
            "  • Configure Nginx with sticky sessions (ip_hash)\n"
            "  • See docs for details: https://offerrall.github.io/FuncToWeb/server-configuration/\n"
            "="*70
        )
    
    if db_location:
        db_path = Path(db_location)
        if db_path.suffix == '':
            db_path.mkdir(parents=True, exist_ok=True)
            set_db_path(db_path)
        else:
            if not db_path.parent.exists():
                raise FileNotFoundError(
                    f"Parent directory '{db_path.parent}' does not exist. "
                    "Create it first or use an existing directory."
                )
            set_db_path(db_path)
    else:
        set_db_path(Path.cwd())
    
    init_db()
    
    funcs = func_or_list if isinstance(func_or_list, list) else [func_or_list]
    
    app_kwargs = {"root_path": root_path}
    
    if fastapi_config:
        conf = fastapi_config.copy()
        if "root_path" in conf:
            conf.pop("root_path") 
        app_kwargs.update(conf)
    
    app = FastAPI(**app_kwargs)
    
    @app.on_event("startup")
    async def startup_cleanup():
        """Background cleanup on startup (non-blocking)."""
        if cleanup_hours > 0:
            await asyncio.to_thread(cleanup_old_files, cleanup_hours)
        
        file_count = get_file_count()
        if file_count > 10000:
            warnings.warn(
                f"Database has {file_count} file references. "
                "Consider enabling cleanup (cleanup_hours > 0) or manually cleaning old files.",
                UserWarning
            )
    
    if template_dir is None:
        template_dir = Path(__file__).parent / "templates"
    else:
        template_dir = Path(template_dir)
    
    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory '{template_dir}' not found.")
    
    templates = Jinja2Templates(directory=str(template_dir))
    app.mount("/static", StaticFiles(directory=template_dir / "static"), name="static")
    
    setup_download_route(app)
    
    if len(funcs) == 1:
        func = funcs[0]
        params = analyze(func)
        setup_single_function_routes(app, func, params, templates, bool(auth))
    else:
        setup_multiple_function_routes(app, funcs, templates, bool(auth))
    
    if auth:
        setup_auth_middleware(app, auth, templates, secret_key)
    
    uvicorn_params = {
        "host": host,
        "port": port,
        "reload": False,
        "limit_concurrency": 100,
        "limit_max_requests": 1000,
        "timeout_keep_alive": 30,
        "h11_max_incomplete_event_size": 16 * 1024 * 1024
    }
    
    if "root_path" in kwargs:
        kwargs.pop("root_path")

    uvicorn_params.update(kwargs)
    
    config = uvicorn.Config(app, **uvicorn_params)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())