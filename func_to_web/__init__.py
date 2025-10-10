import asyncio
import base64
import io
import os
import tempfile
from pathlib import Path
from typing import Annotated, Literal, get_args, get_origin
from datetime import date, time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import Field, TypeAdapter

from .analyze_function import analyze, ParamInfo
from .validate_params import validate_params
from .build_form_fields import build_form_fields


COLOR_PATTERN = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
EMAIL_PATTERN = r'^[^@]+@[^@]+\.[^@]+$'

CHUNK_SIZE = 8 * 1024 * 1024  # 8MB
FILE_BUFFER_SIZE = 8 * 1024 * 1024  # 8MB

def _file_pattern(*extensions):
    """Generate regex pattern for file extensions."""
    exts = [e.lstrip('.').lower() for e in extensions]
    return r'^.+\.(' + '|'.join(exts) + r')$'

# Pre-configured type aliases for common input types
Color = Annotated[str, Field(pattern=COLOR_PATTERN)]
Email = Annotated[str, Field(pattern=EMAIL_PATTERN)]
ImageFile = Annotated[str, Field(pattern=_file_pattern('png', 'jpg', 'jpeg', 'gif', 'webp'))]
DataFile = Annotated[str, Field(pattern=_file_pattern('csv', 'xlsx', 'xls', 'json'))]
TextFile = Annotated[str, Field(pattern=_file_pattern('txt', 'md', 'log'))]
DocumentFile = Annotated[str, Field(pattern=_file_pattern('pdf', 'doc', 'docx'))]


def process_result(result):
    """
    Convert function result to appropriate display format.
    
    Detects PIL Images and matplotlib Figures and converts them to base64.
    All other types are converted to strings.
    
    Args:
        result: The function's return value
        
    Returns:
        dict: {'type': 'image'|'text', 'data': str}
    """
    # PIL Image detection
    try:
        from PIL import Image
        if isinstance(result, Image.Image):
            buffer = io.BytesIO()
            result.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()
            return {
                'type': 'image',
                'data': f'data:image/png;base64,{img_base64}'
            }
    except ImportError:
        pass
    
    # Matplotlib Figure detection
    try:
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        if isinstance(result, Figure):
            buffer = io.BytesIO()
            result.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(result)
            return {
                'type': 'image',
                'data': f'data:image/png;base64,{img_base64}'
            }
    except ImportError:
        pass
    
    # Default: convert to string
    return {
        'type': 'text',
        'data': str(result)
    }


async def save_uploaded_file(uploaded_file, suffix):
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, buffering=FILE_BUFFER_SIZE) as tmp:
        while chunk := await uploaded_file.read(CHUNK_SIZE):
            tmp.write(chunk)
        return tmp.name


def run(func_or_list, host: str="0.0.0.0", port: int=8000, template_dir: str | Path=None):
    """
    Generate and run a web UI for one or more Python functions.
    
    Single function mode: Creates a form at root (/) for the function.
    Multiple functions mode: Creates an index page with links to individual function forms.
    
    Args:
        func_or_list: A single function or list of functions to wrap
        host: Server host address (default: "0.0.0.0")
        port: Server port (default: 8000)
        template_dir: Optional custom template directory
        
    Raises:
        FileNotFoundError: If template directory doesn't exist
        TypeError: If function parameters use unsupported types
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
    
    # Single function mode
    if len(funcs) == 1:
        func = funcs[0]
        params = analyze(func)
        func_name = func.__name__.replace('_', ' ').title()
        
        @app.get("/")
        async def form(request: Request):
            fields = build_form_fields(params)
            return templates.TemplateResponse(
                "form.html",
                {"request": request, "title": func_name, "fields": fields, "submit_url": "/submit"}
            )

        @app.post("/submit")
        async def submit(request: Request):
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
                
                return JSONResponse({
                    "success": True,
                    "result_type": processed['type'],
                    "result": processed['data']
                })
            except Exception as e:
                return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    
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
            route = f"/{func.__name__}"
            submit_route = f"{route}/submit"
            
            def make_form_handler(fn, title, prms, submit_path):
                async def form_view(request: Request):
                    flds = build_form_fields(prms)
                    return templates.TemplateResponse(
                        "form.html",
                        {"request": request, "title": title, "fields": flds, "submit_url": submit_path}
                    )
                return form_view
            
            def make_submit_handler(fn, prms):
                async def submit_view(request: Request):
                    try:
                        form_data = await request.form()
                        data = {}
                        
                        for name, value in form_data.items():
                            if hasattr(value, 'filename'):
                                suffix = os.path.splitext(value.filename)[1]
                                data[name] = await save_uploaded_file(value, suffix)
                            else:
                                data[name] = value
                        
                        validated = validate_params(data, prms)
                        result = fn(**validated)
                        processed = process_result(result)
                        
                        return JSONResponse({
                            "success": True,
                            "result_type": processed['type'],
                            "result": processed['data']
                        })
                    except Exception as e:
                        return JSONResponse({"success": False, "error": str(e)}, status_code=400)
                return submit_view
            
            app.get(route)(make_form_handler(func, func_name, params, submit_route))
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