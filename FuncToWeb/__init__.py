from __future__ import annotations
from typing import get_args, get_origin
from pathlib import Path

from pydantic import TypeAdapter, ValidationError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from .analyze_func import analyze

app = FastAPI()

PACKAGE_DIR = Path(__file__).parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _build_field_for_list(name, ui_type, default):
    """Construye field para list[T]"""
    return {
        'name': name,
        'type': 'select',
        'options': default,
        'default': default
    }


def _build_field_for_number(name, ui_type, default):
    """Construye field para int/float"""
    args = get_args(ui_type)
    base_type = args[0]
    
    field = {
        'name': name,
        'type': 'number',
        'step': '1' if base_type is int else 'any',
        'default': default
    }
    
    for c in args[1].metadata:
        if hasattr(c, 'ge'): field['min'] = c.ge
        if hasattr(c, 'le'): field['max'] = c.le
    
    return field


def _build_field_for_bool(name, default):
    """Construye field para bool"""
    return {
        'name': name,
        'type': 'checkbox',
        'default': default
    }


def _build_field_for_str(name, ui_type, default):
    """Construye field para str"""
    args = get_args(ui_type)
    
    field = {
        'name': name,
        'type': 'text',
        'default': default
    }
    
    for c in args[1].metadata:
        if hasattr(c, 'min_length'): field['minlength'] = c.min_length
        if hasattr(c, 'max_length'): field['maxlength'] = c.max_length
    
    return field


def _build_form_field(name, ui_type, default):
    """Construye un field para el formulario basado en el tipo"""
    origin = get_origin(ui_type)
    
    if origin is list:
        return _build_field_for_list(name, ui_type, default)
    
    args = get_args(ui_type)
    base_type = args[0]
    
    if base_type in (int, float):
        return _build_field_for_number(name, ui_type, default)
    elif base_type is bool:
        return _build_field_for_bool(name, default)
    else:  # str
        return _build_field_for_str(name, ui_type, default)


def _validate_list_value(value, ui_type, default):
    """Valida y convierte valor de list[T]"""
    list_item_type = get_args(ui_type)[0]
    
    if list_item_type is int:
        converted_value = int(value)
    elif list_item_type is float:
        converted_value = float(value)
    elif list_item_type is bool:
        converted_value = value.lower() == 'true'
    else:  # str
        converted_value = value
    
    if converted_value not in default:
        raise ValueError(f"Value '{converted_value}' is not in allowed options: {default}")
    
    return converted_value


def _validate_param(name, value, ui_type, default):
    """Valida un parámetro individual"""
    origin = get_origin(ui_type)
    
    # Manejar list[T]
    if origin is list:
        return _validate_list_value(value, ui_type, default)
    
    # Manejar bool (checkbox)
    args = get_args(ui_type)
    if args and args[0] is bool:
        value = value is not None
    
    # Validar con TypeAdapter
    adapter = TypeAdapter(ui_type)
    return adapter.validate_python(value)


def create_endpoint(func):
    params = analyze(func)
    func_name = func.__name__.replace('_', ' ').title()
    
    @app.get("/")
    async def form_handler(request: Request):
        fields = [
            _build_form_field(name, ui_type, default)
            for name, (ui_type, default) in params.items()
        ]
        
        return templates.TemplateResponse("form.html", {
            "request": request,
            "fields": fields,
            "title": func_name
        })
    
    @app.post("/submit")
    async def submit_handler(request: Request):
        data = dict(await request.form())
        validated = {}
        
        try:
            for name, (ui_type, default) in params.items():
                value = data.get(name)
                validated[name] = _validate_param(name, value, ui_type, default)
            
            result = func(**validated)
            return JSONResponse({"success": True, "result": result})
            
        except ValidationError as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=400)
        except (ValueError, TypeError) as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=400)
        except Exception as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)


def run(func, host: str = "0.0.0.0", port: int = 8000, reload: bool = False, **uvicorn_kwargs):
    import uvicorn
    
    create_endpoint(func)
    uvicorn.run(app, host=host, port=port, reload=reload, **uvicorn_kwargs)