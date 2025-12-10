import asyncio
import inspect
import os
import re
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse, FileResponse as FastAPIFileResponse
from fastapi.templating import Jinja2Templates

from .analyze_function import ParamInfo, analyze
from .validate_params import validate_params
from .build_form_fields import build_form_fields
from .process_result import process_result
from .file_handler import (
    save_uploaded_file,
    get_temp_file,
    cleanup_temp_file,
    create_response_with_files
)

UUID_PATTERN = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')


async def handle_form_submission(
    request: Request, 
    func: Callable, 
    params: dict[str, ParamInfo]
) -> JSONResponse:
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


def setup_download_route(app):
    """Setup file download route.
    
    Args:
        app: FastAPI application instance.
    """
    @app.get("/download/{file_id}")
    async def download_file(file_id: str):
        if not UUID_PATTERN.match(file_id):
            return JSONResponse({"error": "Invalid file ID"}, status_code=400)
        
        file_info = get_temp_file(file_id)
        
        if not file_info:
            return JSONResponse({"error": "File not found"}, status_code=404)
        
        path = file_info['path']
        filename = file_info['filename']
        
        if not os.path.exists(path):
            cleanup_temp_file(file_id, delete_from_disk=False)
            return JSONResponse({"error": "File expired"}, status_code=404)
        
        safe_filename = os.path.basename(filename)
        
        response = FastAPIFileResponse(
            path=path,
            filename=safe_filename,
            media_type='application/octet-stream'
        )
        
        async def cleanup():
            await asyncio.sleep(3600)
            cleanup_temp_file(file_id)
        
        response.background = cleanup
        
        return response


def setup_single_function_routes(app, func: Callable, params: dict, templates: Jinja2Templates, has_auth: bool):
    """Setup routes for single function mode.
    
    Args:
        app: FastAPI application instance.
        func: The function to wrap.
        params: Parameter metadata.
        templates: Jinja2Templates instance.
        has_auth: Whether authentication is enabled.
    """
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
                "has_auth": has_auth
            }
        )

    @app.post("/submit")
    async def submit(request: Request):
        return await handle_form_submission(request, func, params)


def setup_multiple_function_routes(app, funcs: list[Callable], templates: Jinja2Templates, has_auth: bool):
    """Setup routes for multiple functions mode.
    
    Args:
        app: FastAPI application instance.
        funcs: List of functions to wrap.
        templates: Jinja2Templates instance.
        has_auth: Whether authentication is enabled.
    """
    @app.get("/")
    async def index(request: Request):
        tools = [{
            "name": f.__name__.replace('_', ' ').title(),
            "path": f"/{f.__name__}"
        } for f in funcs]
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "tools": tools, "has_auth": has_auth}
        )
    
    for func in funcs:
        params = analyze(func)
        func_name = func.__name__.replace('_', ' ').title()
        description = inspect.getdoc(func)
        route = f"/{func.__name__}"
        submit_route = f"{route}/submit"
        
        def make_form_handler(title: str, prms: dict, desc: str | None, submit_path: str):
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
                        "has_auth": has_auth
                    }
                )
            return form_view
        
        def make_submit_handler(fn: Callable, prms: dict):
            async def submit_view(request: Request):
                return await handle_form_submission(request, fn, prms)
            return submit_view
        
        app.get(route)(make_form_handler(func_name, params, description, submit_route))
        app.post(submit_route)(make_submit_handler(func, params))