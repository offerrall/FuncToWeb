from typing import Annotated, Literal, get_args, get_origin
from pydantic import Field, TypeAdapter
from dataclasses import dataclass
import inspect
from datetime import date

# ========== EXPORTS PÚBLICOS ==========
UI = Annotated
Limits = Field
Selected = Literal

VALID = {int, float, str, bool, date}

# Definir patterns como constantes
COLOR_PATTERN = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
EMAIL_PATTERN = r'^[^@]+@[^@]+\.[^@]+$'
URL_PATTERN = r'^https?://'
PHONE_PATTERN = r'^\+?[0-9\s()-]{10,}$'

# Tipos custom usando las constantes
Color = Annotated[str, Field(pattern=COLOR_PATTERN)]
Email = Annotated[str, Field(pattern=EMAIL_PATTERN)]
URL = Annotated[str, Field(pattern=URL_PATTERN)]
Phone = Annotated[str, Field(pattern=PHONE_PATTERN)]

# Mapeo usando las MISMAS constantes
PATTERN_TO_HTML_TYPE = {
    COLOR_PATTERN: 'color',
    EMAIL_PATTERN: 'email',
    URL_PATTERN: 'url',
    PHONE_PATTERN: 'tel',
}


# ========== DATACLASS ==========
@dataclass
class ParamInfo:
    type: type
    default: any = None
    field_info: any = None


# ========== ANALYZE ==========
def analyze(func):
    result = {}
    
    for name, p in inspect.signature(func).parameters.items():
        default = None if p.default == inspect.Parameter.empty else p.default
        t = p.annotation
        f = None
        
        if get_origin(t) is Annotated:
            args = get_args(t)
            t = args[0]
            if len(args) > 1:
                f = args[1]
        
        if get_origin(t) is Literal:
            opts = get_args(t)
            types = {type(o) for o in opts}
            if len(types) > 1:
                raise TypeError(f"'{name}': mixed types in Literal")
            if default is not None and default not in opts:
                raise ValueError(f"'{name}': default '{default}' not in options {opts}")
            f = t
            t = types.pop()
        
        if t not in VALID:
            raise TypeError(f"'{name}': {t} not supported")
        
        if f and default is not None and hasattr(f, 'metadata'):
            TypeAdapter(Annotated[t, f]).validate_python(default)
        
        result[name] = ParamInfo(t, default, f)
    
    return result


# ========== BUILD FORM ==========
def build_form_fields(params_info):
    """Construye campos HTML desde ParamInfo"""
    fields = []
    
    for name, info in params_info.items():
        field = {
            'name': name, 
            'default': info.default,
            'required': True
        }
        
        # Determinar tipo de input
        if get_origin(info.field_info) is Literal:
            field['type'] = 'select'
            field['options'] = get_args(info.field_info)
            
        elif info.type is bool:
            field['type'] = 'checkbox'
            field['required'] = False
            
        elif info.type is date:
            field['type'] = 'date'
            # Convertir date a string ISO para HTML
            if isinstance(info.default, date):
                field['default'] = info.default.isoformat()
            
        elif info.type in (int, float):
            field['type'] = 'number'
            field['step'] = '1' if info.type is int else 'any'
            
            if info.field_info and hasattr(info.field_info, 'metadata'):
                for c in info.field_info.metadata:
                    cn = type(c).__name__
                    if cn == 'Ge': field['min'] = c.ge
                    elif cn == 'Le': field['max'] = c.le
                    elif cn == 'Gt': field['min'] = c.gt + (1 if info.type is int else 0.01)
                    elif cn == 'Lt': field['max'] = c.lt - (1 if info.type is int else 0.01)
                    
        else:  # str
            field['type'] = 'text'
            
            if info.field_info and hasattr(info.field_info, 'metadata'):
                for c in info.field_info.metadata:
                    cn = type(c).__name__
                    
                    # Pattern - verificar atributo directamente
                    if hasattr(c, 'pattern') and c.pattern:
                        pattern = c.pattern
                        if pattern in PATTERN_TO_HTML_TYPE:
                            field['type'] = PATTERN_TO_HTML_TYPE[pattern]
                        field['pattern'] = pattern
                    
                    # Constraints de string
                    if cn == 'MinLen': 
                        field['minlength'] = c.min_length
                    if cn == 'MaxLen':
                        field['maxlength'] = c.max_length
        
        fields.append(field)
    
    return fields


# ========== VALIDATE ==========
def validate_params(form_data, params_info):
    """Valida y convierte datos del formulario"""
    validated = {}
    
    for name, info in params_info.items():
        value = form_data.get(name)
        
        # Checkbox
        if info.type is bool:
            validated[name] = value is not None
            continue
        
        # Date
        if info.type is date:
            if value:
                validated[name] = date.fromisoformat(value)
            else:
                validated[name] = None
            continue
        
        # Literal/Selected
        if get_origin(info.field_info) is Literal:
            opts = get_args(info.field_info)
            if info.type is int:
                value = int(value)
            elif info.type is float:
                value = float(value)
            
            if value not in opts:
                raise ValueError(f"'{name}': value '{value}' not in {opts}")
            validated[name] = value
            continue
        
        # Normalizar colores: #RGB -> #RRGGBB
        if value and isinstance(value, str) and value.startswith('#') and len(value) == 4:
            value = '#' + ''.join(c*2 for c in value[1:])
        
        # Con Field (incluye patterns, limits, etc.)
        if info.field_info and hasattr(info.field_info, 'metadata'):
            adapter = TypeAdapter(Annotated[info.type, info.field_info])
            validated[name] = adapter.validate_python(value)
        else:
            validated[name] = info.type(value)
    
    return validated


# ========== RUN ==========
def run(func, host="0.0.0.0", port=8000, template_dir="templates"):
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    from fastapi.templating import Jinja2Templates
    from pathlib import Path
    import uvicorn
    
    app = FastAPI()
    params = analyze(func)
    fields = build_form_fields(params)
    func_name = func.__name__.replace('_', ' ').title()
    
    template_path = Path(template_dir)
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template directory '{template_dir}' not found. "
            f"Create it and add 'form.html' template."
        )
    
    templates = Jinja2Templates(directory=str(template_path))
    
    @app.get("/")
    async def form(request: Request):
        return templates.TemplateResponse(
            "form.html",
            {"request": request, "title": func_name, "fields": fields}
        )
    
    @app.post("/submit")
    async def submit(request: Request):
        try:
            data = dict(await request.form())
            validated = validate_params(data, params)
            result = func(**validated)
            return JSONResponse({"success": True, "result": str(result)})
        except Exception as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    
    uvicorn.run(app, host=host, port=port, reload=False)