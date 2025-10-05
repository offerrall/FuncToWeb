from typing import Annotated, get_args, get_origin, Any, Literal
from pydantic import Field, TypeAdapter
from dataclasses import dataclass
import inspect

UI = Annotated
Limits = Field
Selected = Literal

VALID = {int, float, str, bool}


@dataclass
class ParamInfo:
    type: type
    default: Any = None
    field_info: Any = None


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


# TEST
def calc(
    lista: Selected["a", "b", "c"] = "a",
    precio: UI[int, Limits(ge=1, le=1000)] = 100,
    activo: bool = True
):
    pass

for name, info in analyze(calc).items():
    print(f"{name}: type={info.type.__name__}, default={info.default}, field_info={info.field_info}")