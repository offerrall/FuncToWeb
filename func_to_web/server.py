import asyncio
import warnings
from pathlib import Path
from typing import Callable, Any

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config
from .analyze_function import analyze
from .file_handler import cleanup_old_files, get_returned_files_count
from .auth import setup_auth_middleware
from .routes import (
    setup_download_route,
    setup_single_function_routes,
    setup_multiple_function_routes,
    setup_grouped_function_routes
)


def run(
    func_or_list: Callable[..., Any] | list[Callable[..., Any]] | dict[str, list[Callable[..., Any]]], 
    host: str = "0.0.0.0", 
    port: int = 8000, 
    auth: dict[str, str] | None = None,
    secret_key: str | None = None,
    uploads_dir: str | Path = "./uploads",
    returns_dir: str | Path = "./returned_files",
    auto_delete_uploads: bool = True,
    template_dir: str | Path | None = None,
    root_path: str = "",
    fastapi_config: dict[str, Any] | None = None,
    **kwargs
) -> None:
    """Generate and run a web UI for one or more Python functions.
    
    Single function mode: Creates a form at root (/) for the function.
    Multiple functions mode: Creates an index page with links to individual function forms.
    Grouped functions mode: Creates an index page with grouped sections of functions.
    
    Args:
        func_or_list: A single function, list of functions, or dict of {group_name: [functions]}.
        host: Server host address (default: "0.0.0.0").
        port: Server port (default: 8000).
        auth: Optional dictionary of {username: password} for authentication.
        secret_key: Secret key for session signing (required if auth is used). 
                    If None, a random one is generated on startup.
        uploads_dir: Directory for uploaded files (default: "./uploads").
        returns_dir: Directory for returned files (default: "./returned_files").
        auto_delete_uploads: If True, delete uploaded files after processing (default: True).
        template_dir: Optional custom template directory.
        root_path: Prefix for the API path (useful for reverse proxies).
        fastapi_config: Optional dictionary with extra arguments for FastAPI app 
                        (e.g. {'title': 'My App', 'version': '1.0.0'}).
        **kwargs: Extra options passed directly to `uvicorn.Config`.
                  Examples: `ssl_keyfile`, `ssl_certfile`, `log_level`, `workers`.
        
    Raises:
        FileNotFoundError: If template directory doesn't exist.
        TypeError: If function parameters use unsupported types.
    
    Examples:
        Single function:
            run(my_function)
        
        Multiple functions:
            run([func1, func2, func3])
        
        Grouped functions:
            run({
                'Math': [add, subtract, multiply],
                'Text': [uppercase, lowercase]
            })
    
    Notes:
        - Returned files are automatically deleted 1 hour after creation (hardcoded).
        - Cleanup runs on startup and then every hour while server is running.
        - Multiple workers are supported (each worker runs its own cleanup task).
    """

    uploads_path = Path(uploads_dir)
    returns_path = Path(returns_dir)
    uploads_path.mkdir(parents=True, exist_ok=True)
    returns_path.mkdir(parents=True, exist_ok=True)

    config.UPLOADS_DIR = uploads_path
    config.RETURNS_DIR = returns_path
    config.AUTO_DELETE_UPLOADS = auto_delete_uploads
    
    is_grouped = isinstance(func_or_list, dict)
    is_single = not isinstance(func_or_list, (list, dict))
    
    if is_grouped:
        grouped_funcs = func_or_list
        funcs = []
        for group_functions in grouped_funcs.values():
            funcs.extend(group_functions)
    elif is_single:
        funcs = [func_or_list]
    else:
        funcs = func_or_list

    app_kwargs = {"root_path": root_path}
    
    if fastapi_config:
        conf = fastapi_config.copy()
        if "root_path" in conf:
            conf.pop("root_path") 
        app_kwargs.update(conf)
    
    app = FastAPI(**app_kwargs)
    
    @app.on_event("startup")
    async def startup_cleanup():
        """Cleanup old files on startup and run periodic cleanup task."""
        await asyncio.to_thread(cleanup_old_files)

        file_count = get_returned_files_count()
        if file_count > 10000:
            warnings.warn(
                f"Returns directory has {file_count} files. "
                "Consider manually cleaning old files or restarting the server.",
                UserWarning
            )
        
        async def periodic_cleanup_task():
            """Run cleanup every hour to remove files older than 1 hour."""
            while True:
                await asyncio.sleep(3600)
                await asyncio.to_thread(cleanup_old_files)
        
        asyncio.create_task(periodic_cleanup_task())

    if template_dir is None:
        template_dir = Path(__file__).parent / "templates"
    else:
        template_dir = Path(template_dir)
    
    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory '{template_dir}' not found.")
    
    templates = Jinja2Templates(directory=str(template_dir))
    app.mount("/static", StaticFiles(directory=template_dir / "static"), name="static")
    
    setup_download_route(app)
    
    if is_single:
        func = funcs[0]
        params = analyze(func)
        setup_single_function_routes(app, func, params, templates, bool(auth))
    elif is_grouped:
        setup_grouped_function_routes(app, grouped_funcs, templates, bool(auth))
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
    
    config_obj = uvicorn.Config(app, **uvicorn_params)
    server = uvicorn.Server(config_obj)
    asyncio.run(server.serve())