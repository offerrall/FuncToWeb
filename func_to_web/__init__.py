import asyncio
import os
import tempfile
import uuid
import json
import inspect
from pathlib import Path
from typing import Annotated, Literal, Callable, Any
from datetime import date, time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse as FastAPIFileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import Field

from .analyze_function import analyze, ParamInfo
from .validate_params import validate_params
from .build_form_fields import build_form_fields
from .process_result import process_result

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
    template_dir: str | Path | None = None
) -> None:
    """Generate and run a web UI for one or more Python functions.
    
    Single function mode: Creates a form at root (/) for the function.
    Multiple functions mode: Creates an index page with links to individual function forms.
    
    Args:
        func_or_list: A single function or list of functions to wrap.
        host: Server host address (default: "0.0.0.0").
        port: Server port (default: 8000).
        template_dir: Optional custom template directory.
        
    Raises:
        FileNotFoundError: If template directory doesn't exist.
        TypeError: If function parameters use unsupported types.
    """
    
    funcs = func_or_list if isinstance(func_or_list, list) else [func_or_list]
    
    app = FastAPI()
    
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
                    "submit_url": "/submit"
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
                {"request": request, "tools": tools}
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
                            "submit_url": submit_path
                        }
                    )
                return form_view
            
            def make_submit_handler(fn: Callable, prms: dict[str, ParamInfo]):
                async def submit_view(request: Request):
                    return await handle_form_submission(request, fn, prms)
                return submit_view
            
            app.get(route)(make_form_handler(func_name, params, description, submit_route))
            app.post(submit_route)(make_submit_handler(func, params))
    
    config = uvicorn.Config(
        app, 
        host=host, 
        port=port, 
        reload=False,
        limit_concurrency=100,
        limit_max_requests=1000,
        timeout_keep_alive=30,
        h11_max_incomplete_event_size=16 * 1024 * 1024
    )
    server = uvicorn.Server(config)
    asyncio.run(server.serve())