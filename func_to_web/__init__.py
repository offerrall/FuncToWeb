import asyncio
import base64
import inspect
import io
import os
import tempfile
from dataclasses import dataclass
from datetime import date, time
from pathlib import Path
from typing import Annotated, Literal, get_args, get_origin, Union
import types

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import Field, TypeAdapter

VALID = {int, float, str, bool, date, time}

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

PATTERN_TO_HTML_TYPE = {
    COLOR_PATTERN: 'color',
    EMAIL_PATTERN: 'email',
}


@dataclass
class ParamInfo:
    """Metadata about a function parameter."""
    type: type # The base type (int, float, str, bool, date, time)
    default: any = None # The default value, or None if required
    field_info: any = None # Additional Field or Literal info
    dynamic_func: any = None # Store the dynamic function for later re-execution
    is_optional: bool = False # True if parameter is Optional (i.e., allows None)


def analyze(func):
    """
    Analyze a function's signature and extract parameter metadata.
    
    Args:
        func: The function to analyze
        
    Returns:
        dict: Mapping of parameter names to ParamInfo objects
        
    Raises:
        TypeError: If parameter type is not supported
        ValueError: If default value doesn't match Literal options
    """
    result = {}
    
    for name, p in inspect.signature(func).parameters.items():
        default = None if p.default == inspect.Parameter.empty else p.default
        t = p.annotation
        f = None
        dynamic_func = None
        is_optional = False
        
        # Extract base type from Annotated
        if get_origin(t) is Annotated:
            args = get_args(t)
            t = args[0]
            if len(args) > 1:
                f = args[1]
        
        # Check for Union types (including | None syntax)
        if get_origin(t) is types.UnionType or str(get_origin(t)) == 'typing.Union':
            union_args = get_args(t)
            
            # Check if None is in the union (making it optional)
            if type(None) in union_args:
                is_optional = True
                # Remove None from the types and get the actual type
                non_none_types = [arg for arg in union_args if arg is not type(None)]
                
                if len(non_none_types) == 0:
                    raise TypeError(f"'{name}': Cannot have only None type")
                elif len(non_none_types) > 1:
                    raise TypeError(f"'{name}': Union with multiple non-None types not supported")
                
                # Extract the actual type
                t = non_none_types[0]
                
                # Check again if this is Annotated
                if get_origin(t) is Annotated:
                    args = get_args(t)
                    t = args[0]
                    if len(args) > 1 and f is None:
                        f = args[1]
        
        # Handle Literal types (dropdowns)
        if get_origin(t) is Literal:
            opts = get_args(t)
            
            # Check if opts contains a single callable (dynamic Literal)
            if len(opts) == 1 and callable(opts[0]):
                dynamic_func = opts[0]
                result_value = dynamic_func()
                
                # Convert result to tuple properly
                if isinstance(result_value, (list, tuple)):
                    opts = tuple(result_value)
                else:
                    opts = (result_value,)
            
            # Validate options
            if opts:
                types_set = {type(o) for o in opts}
                if len(types_set) > 1:
                    raise TypeError(f"'{name}': mixed types in Literal")
                if default is not None and default not in opts:
                    raise ValueError(f"'{name}': default '{default}' not in options {opts}")
                
                f = Literal[opts] if len(opts) > 0 else t
                t = types_set.pop() if types_set else type(None)
            else:
                t = type(None)
        
        if t not in VALID:
            raise TypeError(f"'{name}': {t} not supported")
        
        # Validate default value against field constraints
        if f and default is not None and hasattr(f, 'metadata'):
            TypeAdapter(Annotated[t, f]).validate_python(default)
        
        result[name] = ParamInfo(t, default, f, dynamic_func, is_optional)
    
    return result


def build_form_fields(params_info):
    """
    Build form field specifications from parameter metadata.
    Re-executes dynamic functions to get fresh options.
    
    Args:
        params_info: dict mapping parameter names to ParamInfo objects
        
    Returns:
        list: List of field dictionaries for template rendering
    """
    fields = []
    
    for name, info in params_info.items():
        field = {
            'name': name, 
            'default': info.default,
            'required': not info.is_optional,
            'is_optional': info.is_optional,
            'optional_enabled': info.default is not None
        }
        
        # Dropdown select
        if get_origin(info.field_info) is Literal:
            field['type'] = 'select'
            
            # Re-execute dynamic function if present
            if info.dynamic_func is not None:
                result_value = info.dynamic_func()
                
                # Convert result to tuple properly
                if isinstance(result_value, (list, tuple)):
                    fresh_options = tuple(result_value)
                else:
                    fresh_options = (result_value,)
                
                field['options'] = fresh_options
                info.field_info = Literal[fresh_options]
            else:
                field['options'] = get_args(info.field_info)
            
        # Checkbox
        elif info.type is bool:
            field['type'] = 'checkbox'
            field['required'] = False
            
        # Date picker
        elif info.type is date:
            field['type'] = 'date'
            if isinstance(info.default, date):
                field['default'] = info.default.isoformat()
        
        # Time picker
        elif info.type is time:
            field['type'] = 'time'
            if isinstance(info.default, time):
                field['default'] = info.default.strftime('%H:%M')
            
        # Number input
        elif info.type in (int, float):
            field['type'] = 'number'
            field['step'] = '1' if info.type is int else 'any'
            
            # Extract numeric constraints from Pydantic Field
            if info.field_info and hasattr(info.field_info, 'metadata'):
                for c in info.field_info.metadata:
                    cn = type(c).__name__
                    if cn == 'Ge': field['min'] = c.ge
                    elif cn == 'Le': field['max'] = c.le
                    elif cn == 'Gt': field['min'] = c.gt + (1 if info.type is int else 0.01)
                    elif cn == 'Lt': field['max'] = c.lt - (1 if info.type is int else 0.01)
                    
        # Text/email/color/file input
        else:
            field['type'] = 'text'
            
            if info.field_info and hasattr(info.field_info, 'metadata'):
                for c in info.field_info.metadata:
                    cn = type(c).__name__
                    
                    # Check for pattern constraints
                    if hasattr(c, 'pattern') and c.pattern:
                        pattern = c.pattern
                        
                        # File input detection
                        if pattern.startswith(r'^.+\.(') and pattern.endswith(r')$'):
                            field['type'] = 'file'
                            exts = pattern[6:-2].split('|')
                            field['accept'] = '.' + ',.'.join(exts)
                        # Special input types (color, email)
                        elif pattern in PATTERN_TO_HTML_TYPE:
                            field['type'] = PATTERN_TO_HTML_TYPE[pattern]
                        
                        field['pattern'] = pattern
                    
                    # String length constraints
                    if cn == 'MinLen': 
                        field['minlength'] = c.min_length
                    if cn == 'MaxLen':
                        field['maxlength'] = c.max_length
        
        fields.append(field)
    
    return fields

def validate_params(form_data, params_info):
    """
    Validate and convert form data to function parameters.
    Re-executes dynamic functions to get current valid options.
    
    Args:
        form_data: Raw form data from request
        params_info: Parameter metadata from analyze()
        
    Returns:
        dict: Validated parameters ready for function call
        
    Raises:
        ValueError: If validation fails
    """
    validated = {}
    
    for name, info in params_info.items():
        value = form_data.get(name)
        
        # Check if optional field is disabled
        optional_toggle_name = f"{name}_optional_toggle"
        if info.is_optional and optional_toggle_name not in form_data:
            # Optional field is disabled, send None
            validated[name] = None
            continue
        
        # Checkbox handling
        if info.type is bool:
            validated[name] = value is not None
            continue
        
        # Date conversion
        if info.type is date:
            if value:
                validated[name] = date.fromisoformat(value)
            else:
                validated[name] = None
            continue
        
        # Time conversion
        if info.type is time:
            if value:
                validated[name] = time.fromisoformat(value)
            else:
                validated[name] = None
            continue
        
        # Literal validation
        if get_origin(info.field_info) is Literal:
            # Convert to correct type
            if info.type is int:
                value = int(value)
            elif info.type is float:
                value = float(value)
            
            # Only validate against options if Literal is NOT dynamic
            # Dynamic literals can change between form render and submit
            if info.dynamic_func is None:
                # Static literal - validate against fixed options
                opts = get_args(info.field_info)
                if value not in opts:
                    raise ValueError(f"'{name}': value '{value}' not in {opts}")
            # else: Dynamic literal - skip validation, trust the value from the form
            
            validated[name] = value
            continue
        
        # Expand shorthand hex colors (#RGB -> #RRGGBB)
        if value and isinstance(value, str) and value.startswith('#') and len(value) == 4:
            value = '#' + ''.join(c*2 for c in value[1:])
        
        # Pydantic validation with constraints
        if info.field_info and hasattr(info.field_info, 'metadata'):
            adapter = TypeAdapter(Annotated[info.type, info.field_info])
            validated[name] = adapter.validate_python(value)
        else:
            validated[name] = info.type(value) if value else None
    
    return validated


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