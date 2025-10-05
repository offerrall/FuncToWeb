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
        field = {'name': name, 'default': info.default}
        
        # Determinar tipo de input
        if get_origin(info.field_info) is Literal:
            # Select dropdown
            field['type'] = 'select'
            field['options'] = get_args(info.field_info)
        elif info.type is bool:
            field['type'] = 'checkbox'
        elif info.type in (int, float):
            field['type'] = 'number'
            field['step'] = '1' if info.type is int else 'any'
            
            # Extraer constraints
            if info.field_info and hasattr(info.field_info, 'metadata'):
                for c in info.field_info.metadata:
                    cn = type(c).__name__
                    if cn == 'Ge': field['min'] = c.ge
                    elif cn == 'Le': field['max'] = c.le
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


# ========== RUN (FASTAPI) ==========
def run(func, host="0.0.0.0", port=8000, reload=False):
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, HTMLResponse
    import uvicorn
    
    app = FastAPI()
    params = analyze(func)
    fields = build_form_fields(params)
    func_name = func.__name__.replace('_', ' ').title()
    
    # HTML inline (minimalista)
    html_template = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{title}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:sans-serif;padding:2rem;max-width:500px;margin:0 auto}}.field{{margin-bottom:1rem}}label{{display:block;margin-bottom:0.5rem}}input,select{{width:100%;padding:0.5rem;border:1px solid #ccc;border-radius:4px}}button{{padding:0.75rem 1.5rem;background:#007bff;color:white;border:none;border-radius:4px;cursor:pointer}}button:hover{{background:#0056b3}}</style>
</head><body><h1>{title}</h1><form id="form">{fields}<button type="submit">Submit</button></form>
<div id="result" style="margin-top:1rem;padding:1rem;background:#d4edda;border-radius:4px;display:none"></div>
<script>
document.getElementById('form').addEventListener('submit',async(e)=>{{e.preventDefault();const d=await fetch('/submit',{{method:'POST',body:new FormData(e.target)}});const r=await d.json();document.getElementById('result').textContent=JSON.stringify(r.result,null,2);document.getElementById('result').style.display='block'}});
</script></body></html>"""
    
    def render_field(f):
        if f['type'] == 'checkbox':
            return f'<div class="field"><label><input type="checkbox" name="{f["name"]}" {"checked" if f.get("default") else ""}> {f["name"]}</label></div>'
        elif f['type'] == 'select':
            opts = ''.join(f'<option value="{o}">{o}</option>' for o in f['options'])
            return f'<div class="field"><label>{f["name"]}</label><select name="{f["name"]}">{opts}</select></div>'
        else:
            attrs = f'type="{f["type"]}" name="{f["name"]}"'
            if f.get('min') is not None: attrs += f' min="{f["min"]}"'
            if f.get('max') is not None: attrs += f' max="{f["max"]}"'
            if f.get('step'): attrs += f' step="{f["step"]}"'
            if f.get('default') is not None: attrs += f' value="{f["default"]}"'
            return f'<div class="field"><label>{f["name"]}</label><input {attrs}></div>'
    
    html = html_template.format(title=func_name, fields=''.join(render_field(f) for f in fields))
    
    @app.get("/")
    async def form():
        return HTMLResponse(html)
    
    @app.post("/submit")
    async def submit(request: Request):
        try:
            data = dict(await request.form())
            validated = validate_params(data, params)
            result = func(**validated)
            return JSONResponse({"success": True, "result": result})
        except Exception as e:
            return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    
    uvicorn.run(app, host=host, port=port, reload=False)

if __name__ == "__main__":
    def test_func(name: str = "World", times: int = Limits(1, ge=1, le=5), excited: bool = False, mood: Selected['happy', 'sad', 'neutral'] = 'neutral'):
        greeting = f"Hello, {name}" + ("!" * times if excited else ".")
        return {"greeting": greeting, "mood": mood}
    
    run(test_func)