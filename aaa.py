from typing import Annotated, get_args, get_origin, Any
from pydantic import Field
from dataclasses import dataclass
import inspect

UI = Annotated
Limits = Field

VALID_TYPES = {int, float, str, bool}

@dataclass
class ParamInfo:
    type: type
    default: Any = None
    field_info: Any = None


def analyze(func):
    result = {}
    
    for name, p in inspect.signature(func).parameters.items():
        default = None if p.default == inspect.Parameter.empty else p.default
        param_type = p.annotation
        field_info = None
        
        if get_origin(p.annotation) is Annotated:
            args = get_args(p.annotation)
            param_type = args[0]
            if len(args) > 1:
                field_info = args[1]

        if param_type not in VALID_TYPES:
            raise ValueError(f"Unsupported type for parameter '{name}': {param_type}")
        
        result[name] = ParamInfo(
            type=param_type,
            default=default,
            field_info=field_info
        )
    
    return result


# TEST
def calc(
    precio: UI[int, Limits(ge=1, le=1000)],
    descuento: UI[int, Limits(ge=0, le=100)] = 15,
    activo: bool = True
):
    pass

for name, info in analyze(calc).items():
    print(f"{name}: {info}")