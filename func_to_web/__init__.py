import asyncio
import os
import tempfile
import uuid
import json
import inspect
import secrets
from pathlib import Path
from typing import Annotated, Literal, Callable, Any
from datetime import date, time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse as FastAPIFileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pydantic import Field

from .analyze_function import analyze, ParamInfo
from .validate_params import validate_params
from .build_form_fields import build_form_fields
from .process_result import process_result

__version__ = "0.9.3"

CHUNK_SIZE = 8 * 1024 * 1024  # 8MB
FILE_BUFFER_SIZE = 8 * 1024 * 1024  # 8MB
TEMP_FILES_REGISTRY = Path(tempfile.gettempdir()) / "func_to_web_files.json"


async def save_uploaded_file(uploaded_file: Any, suffix: str) -> str:
    """Save an uploaded file to a temporary location.
    
    Args:
        uploaded_file: The uploaded file object from FastAPI.
        suffix: File extension to use for the temp file.
        
    Returns:
        Path to the saved temporary file.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, buffering=FILE_BUFFER_SIZE) as tmp:
        while chunk := await uploaded_file.read(CHUNK_SIZE):
            tmp.write(chunk)
        return tmp.name

def register_temp_file(file_id: str, path: str, filename: str) -> None:
    """Register a temp file for download.
    
    Args:
        file_id: Unique identifier for the file.
        path: File system path to the temporary file.
        filename: Original filename for download.
    """
    try:
        if TEMP_FILES_REGISTRY.exists():
            with open(TEMP_FILES_REGISTRY, 'r') as f:
                registry = json.load(f)
        else:
            registry = {}
        
        registry[file_id] = {'path': path, 'filename': filename}
        
        with open(TEMP_FILES_REGISTRY, 'w') as f:
            json.dump(registry, f)
    except:
        pass

def get_temp_file(file_id: str) -> dict[str, str] | None:
    """Get temp file info from registry.
    
    Args:
        file_id: Unique identifier for the file.
        
    Returns:
        Dictionary with 'path' and 'filename' keys, or None if not found.
    """
    try:
        if not TEMP_FILES_REGISTRY.exists():
            return None
        
        with open(TEMP_FILES_REGISTRY, 'r') as f:
            registry = json.load(f)
        
        return registry.get(file_id)
    except:
        return None

def cleanup_temp_file(file_id: str) -> None:
    """Remove temp file and its registry entry.
    
    Args:
        file_id: Unique identifier for the file.
    """
    try:
        if not TEMP_FILES_REGISTRY.exists():
            return
        
        with open(TEMP_FILES_REGISTRY, 'r') as f:
            registry = json.load(f)
        
        if file_id in registry:
            path = registry[file_id]['path']
            try:
                os.unlink(path)
            except:
                pass
            
            del registry[file_id]
            
            with open(TEMP_FILES_REGISTRY, 'w') as f:
                json.dump(registry, f)
    except:
        pass

def create_response_with_files(processed: dict[str, Any]) -> dict[str, Any]:
    """Create JSON response with file downloads.
    
    Args:
        processed: Processed result from process_result().
        
    Returns:
        Response dictionary with file IDs and metadata.
    """
    response = {"success": True, "result_type": processed['type']}
    
    if processed['type'] == 'download':
        file_id = str(uuid.uuid4())
        register_temp_file(file_id, processed['path'], processed['filename'])
        response['file_id'] = file_id
        response['filename'] = processed['filename']
    
    elif processed['type'] == 'downloads':
        files = []
        for f in processed['files']:
            file_id = str(uuid.uuid4())
            register_temp_file(file_id, f['path'], f['filename'])
            files.append({
                'file_id': file_id,
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


async def handle_form_submission(request: Request, func: Callable, params: dict[str, ParamInfo]) -> JSONResponse:
    """Handle form submission for any function.
    
    Args:
        request: FastAPI request object.
        func: Function to call with validated parameters.
        params: Parameter metadata from analyze().
        
    Returns:
        JSON response with result or error.
    """
    try:
        form_data = await request.form()
        data = {}
        
        for name, value in form_data.items():
            if hasattr(value, 'filename'):
                suffix = os.path.splitext(value.filename)[1]
                data[name] = await save_uploaded_file(value, suffix)
            else:
                data[name] = value
        
        validated = validate_params(data, params)
        if inspect.iscoroutinefunction(func):
            result = await func(**validated)
        else:
            result = func(**validated)
        processed = process_result(result)
        response = create_response_with_files(processed)
        
        return JSONResponse(response)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)

def run(
    func_or_list: Callable[..., Any] | list[Callable[..., Any]], 
    host: str = "0.0.0.0", 
    port: int = 8000, 
    auth: dict[str, str] | None = None,
    secret_key: str | None = None,
    template_dir: str | Path | None = None,
    root_path: str = "",
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
        fastapi_config: Optional dictionary with extra arguments for FastAPI app 
                        (e.g. {'title': 'My App', 'version': '1.0.0'}).
        **kwargs: Extra options passed directly to `uvicorn.Config`.
                  Examples: `ssl_keyfile`, `ssl_certfile`, `workers`, `log_level`.
        
    Raises:
        FileNotFoundError: If template directory doesn't exist.
        TypeError: If function parameters use unsupported types.
    """
    
    funcs = func_or_list if isinstance(func_or_list, list) else [func_or_list]
    
    # 1. Prepare FastAPI configuration
    app_kwargs = {"root_path": root_path}
    
    if fastapi_config:
        conf = fastapi_config.copy()
        if "root_path" in conf:
            conf.pop("root_path") 
        app_kwargs.update(conf)
    
    # Instantiate FastAPI with combined config
    app = FastAPI(**app_kwargs)
    
    if template_dir is None:
        template_dir = Path(__file__).parent / "templates"
    else:
        template_dir = Path(template_dir)
    
    if not template_dir.exists():
        raise FileNotFoundError(
            f"Template directory '{template_dir}' not found."
        )
    
    templates = Jinja2Templates(directory=str(template_dir))
    app.mount("/static", StaticFiles(directory=template_dir / "static"), name="static")
    
    # Download endpoint for streaming files
    @app.get("/download/{file_id}")
    async def download_file(file_id: str):
        file_info = get_temp_file(file_id)
        
        if not file_info:
            return JSONResponse({"error": "File not found"}, status_code=404)
        
        path = file_info['path']
        filename = file_info['filename']
        
        if not os.path.exists(path):
            cleanup_temp_file(file_id)
            return JSONResponse({"error": "File expired"}, status_code=404)
        
        response = FastAPIFileResponse(
            path=path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
        # Cleanup after sending
        async def cleanup():
            cleanup_temp_file(file_id)
        
        response.background = cleanup
        
        return response
    
    # Single function mode
    if len(funcs) == 1:
        func = funcs[0]
        params = analyze(func)
        func_name = func.__name__.replace('_', ' ').title()
        description = inspect.getdoc(func)
        
        @app.get("/")
        async def form(request: Request):
            fields = build_form_fields(params)
            return templates.TemplateResponse(
                "form.html",
                {
                    "request": request, 
                    "title": func_name, 
                    "description": description,
                    "fields": fields, 
                    "submit_url": "/submit",
                    "show_back_button": False,
                    "has_auth": bool(auth)
                }
            )

        @app.post("/submit")
        async def submit(request: Request):
            return await handle_form_submission(request, func, params)
    
    # Multiple functions mode
    else:
        @app.get("/")
        async def index(request: Request):
            tools = [{
                "name": f.__name__.replace('_', ' ').title(),
                "path": f"/{f.__name__}"
            } for f in funcs]
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "tools": tools, "has_auth": bool(auth)}
            )
        
        for func in funcs:
            params = analyze(func)
            func_name = func.__name__.replace('_', ' ').title()
            description = inspect.getdoc(func)
            route = f"/{func.__name__}"
            submit_route = f"{route}/submit"
            
            def make_form_handler(title: str, prms: dict[str, ParamInfo], desc: str | None, submit_path: str):
                async def form_view(request: Request):
                    flds = build_form_fields(prms)
                    return templates.TemplateResponse(
                        "form.html",
                        {
                            "request": request, 
                            "title": title, 
                            "description": desc,
                            "fields": flds, 
                            "submit_url": submit_path,
                            "show_back_button": True,
                            "has_auth": bool(auth)
                        }
                    )
                return form_view
            
            def make_submit_handler(fn: Callable, prms: dict[str, ParamInfo]):
                async def submit_view(request: Request):
                    return await handle_form_submission(request, fn, prms)
                return submit_view
            
            app.get(route)(make_form_handler(func_name, params, description, submit_route))
            app.post(submit_route)(make_submit_handler(func, params))
    
    if auth:
        key = secret_key or secrets.token_hex(32)
        
        # 1. Define Auth Middleware (INNER)
        @app.middleware("http")
        async def auth_middleware(request: Request, call_next):
            path = request.url.path
            
            # Allow public paths: login page, auth endpoint, and static assets
            if path in ["/login", "/auth"] or path.startswith("/static"):
                return await call_next(request)
            
            # Check for valid session
            if not request.session.get("user"):
                # If API call (AJAX), return 401
                if "application/json" in request.headers.get("accept", ""):
                     return JSONResponse({"error": "Unauthorized"}, status_code=401)
                # If browser navigation, redirect to login
                return RedirectResponse(url="/login")
            
            return await call_next(request)

        # 2. Add SessionMiddleware (OUTER - runs first)
        # https_only=False is safer for local dev/proxies. 
        app.add_middleware(SessionMiddleware, secret_key=key, https_only=False)

        @app.get("/login")
        async def login_page(request: Request):
            # If already logged in, go home
            if request.session.get("user"):
                return RedirectResponse(url="/")
            return templates.TemplateResponse("login.html", {"request": request})

        @app.post("/auth")
        async def authenticate(request: Request):
            try:
                form = await request.form()
                username = form.get("username")
                password = form.get("password")
                
                if username in auth:
                    # Safe comparison against Timing Attacks
                    if secrets.compare_digest(auth[username], password):
                        request.session["user"] = username
                        return RedirectResponse(url="/", status_code=303)
                
                return templates.TemplateResponse(
                    "login.html", 
                    {"request": request, "error": "Invalid credentials"}
                )
            except Exception:
                return templates.TemplateResponse(
                    "login.html", 
                    {"request": request, "error": "Login failed"}
                )

        @app.get("/logout")
        async def logout(request: Request):
            request.session.clear()
            return RedirectResponse(url="/login")

    # 2. Prepare Uvicorn configuration
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