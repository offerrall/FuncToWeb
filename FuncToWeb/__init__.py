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

def create_endpoint(func):
    params = analyze(func)
    func_name = func.__name__.replace('_', ' ').title()
    
    @app.get("/")
    async def form_handler(request: Request):
        fields = []
        for name, (ui_type, default, ui_metadata) in params.items():
            field = {'name': name, 'default': default}
            
            # Detectar list[T] - es el tipo raw, no tiene metadata
            origin = get_origin(ui_type)
            if origin is list:
                field['type'] = 'select'
                field['options'] = default
                fields.append(field)
                continue
            
            # Detectar ColorUi usando metadata explícita
            if ui_metadata and ui_metadata.get('is_color'):
                field['type'] = 'color'
                fields.append(field)
                continue
            
            args = get_args(ui_type)
            base_type = args[0]
            
            if base_type in (int, float):
                field['type'] = 'number'
                field['step'] = '1' if base_type is int else 'any'
                for c in args[1].metadata:
                    if hasattr(c, 'ge'): field['min'] = c.ge
                    if hasattr(c, 'le'): field['max'] = c.le
            elif base_type is bool:
                field['type'] = 'checkbox'
            else:
                field['type'] = 'text'
                for c in args[1].metadata:
                    if hasattr(c, 'min_length'): field['minlength'] = c.min_length
                    if hasattr(c, 'max_length'): field['maxlength'] = c.max_length
            
            fields.append(field)
        
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
            for name, (ui_type, default, ui_metadata) in params.items():
                value = data.get(name)
                
                # Manejar list[T] - el valor viene directo del select
                origin = get_origin(ui_type)
                if origin is list:
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
                    
                    validated[name] = converted_value
                    continue

                # Manejar bool (checkbox)
                args = get_args(ui_type)
                if args and args[0] is bool:
                    value = value is not None

                # Validar - el TypeAdapter ahora tiene el pattern correcto de ColorUi
                adapter = TypeAdapter(ui_type)
                validated[name] = adapter.validate_python(value)
            
            try:
                result = func(**validated)
            except Exception as e:
                print(f"Function execution error: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)
            print(f"Result: {result}")
            return JSONResponse({"success": True, "result": result})
        except ValidationError as e:
            # Extraer mensaje más claro para errores de validación
            error_msg = str(e)
            if "String should match pattern" in error_msg:
                error_msg = "Invalid color format. Use hex format: #RRGGBB (e.g., #FF5733)"
            print(f"Validation error: {e}")
            return JSONResponse({"success": False, "error": error_msg}, status_code=400)
        except (ValueError, TypeError) as e:
            print(f"Value/Type error: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=400)


def run(func, host: str = "0.0.0.0", port: int = 8000, reload: bool = False, **uvicorn_kwargs):
    import uvicorn
    
    create_endpoint(func)
    uvicorn.run(app, host=host, port=port, reload=reload, **uvicorn_kwargs)