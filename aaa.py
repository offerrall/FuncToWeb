from typing import Annotated, get_args, get_origin
from pydantic import Field
import inspect

UI = Annotated
Limits = Field


def analyze(func):
    result = {}
    
    for name, p in inspect.signature(func).parameters.items():
        info = {}
        info['default'] = None if p.default == inspect.Parameter.empty else p.default
        info['type'] = p.annotation

        if get_origin(p.annotation) is Annotated:
            args = get_args(p.annotation)
            info['type'] = args[0]
            if len(args) > 1:
                info['field_info'] = args[1]

        result[name] = info
    
    return result


# TEST
def calc(
    precio: UI[int, Limits(ge=1, le=1000)],
    descuento: UI[int, Limits(ge=0, le=100)] = 15,
    activo: bool = True
):
    pass

for name, info in analyze(calc).items():
    print(f"{name}: type={info['type'].__name__}, default={info['default']}, field_info={info['field_info']}")