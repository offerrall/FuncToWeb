from typing import Annotated, Literal, get_args, get_origin
from pydantic import Field, TypeAdapter
from dataclasses import dataclass
import inspect

# ========== EXPORTS PÚBLICOS ==========
UI = Annotated
Limits = Field
Selected = Literal

VALID = {int, float, str, bool}


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
            'required': True  # Todos los campos son obligatorios
        }
        
        # Determinar tipo de input
        if get_origin(info.field_info) is Literal:
            # Select dropdown
            field['type'] = 'select'
            field['options'] = get_args(info.field_info)
        elif info.type is bool:
            field['type'] = 'checkbox'
            field['required'] = False  # Checkboxes no usan required (son true/false)
        elif info.type in (int, float):
            field['type'] = 'number'
            field['step'] = '1' if info.type is int else 'any'
            
            # Extraer constraints
            if info.field_info and hasattr(info.field_info, 'metadata'):
                for c in info.field_info.metadata:
                    cn = type(c).__name__
                    if cn == 'Ge': field['min'] = c.ge
                    elif cn == 'Le': field['max'] = c.le
                    elif cn == 'Gt': field['min'] = c.gt + (1 if info.type is int else 0.01)
                    elif cn == 'Lt': field['max'] = c.lt - (1 if info.type is int else 0.01)
        else:  # str
            field['type'] = 'text'
            
            # Extraer constraints
            if info.field_info and hasattr(info.field_info, 'metadata'):
                for c in info.field_info.metadata:
                    cn = type(c).__name__
                    if cn == 'MinLen': field['minlength'] = c.min_length
                    elif cn == 'MaxLen': field['maxlength'] = c.max_length
        
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
        
        # Con Limits (usar TypeAdapter)
        if info.field_info and hasattr(info.field_info, 'metadata'):
            adapter = TypeAdapter(Annotated[info.type, info.field_info])
            validated[name] = adapter.validate_python(value)
        else:
            # Tipo simple sin constraints
            validated[name] = info.type(value)
    
    return validated


# ========== RUN (FASTAPI + JINJA2) ==========
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
    
    # Verificar que exista el directorio de templates
    template_path = Path(template_dir)
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template directory '{template_dir}' not found. "
            f"Create it and add 'form.html' template."
        )
    
    # Configurar Jinja2
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
            return JSONResponse({"success": True, "result": result})
        except Exception as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    
    print(f"🚀 Server starting at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=False)


# ========== EJEMPLO ==========
if __name__ == "__main__":
    def test_func(
        times: UI[int, Limits(ge=1, le=5)],
        name: str = "World",
        name_limit: UI[str, Limits(min_length=3, max_length=20)] = "User",
        excited: bool = False,
        mood: Selected['happy', 'sad', 'neutral'] = 'neutral'
    ):
        greeting = f"Hello, {name}" + ("!" * times if excited else ".")
        return {"greeting": greeting, "mood": mood, "name_limit": name_limit}
    
    run(test_func)