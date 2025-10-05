from typing import get_args, get_origin
from pydantic import TypeAdapter
import inspect

from .ui_types import *


def analyze(func):
    types_map = {int: IntUi, float: FloatUi, str: StrUi, bool: BoolUi}
    sig = inspect.signature(func)
    params = {}

    for name, param in sig.parameters.items():
        annotation = func.__annotations__.get(name)
        
        if not annotation:
            raise TypeError("All parameters must have type hints.")

        real_type = annotation
        args_type = get_args(real_type)
        origin_type = get_origin(real_type)
        default = param.default if param.default != inspect.Parameter.empty else None
    
        # Detectar list[T] con default
        if origin_type is list:
            if not args_type:
                raise TypeError(f"Parameter '{name}': list must specify a type, e.g., list[str], list[int]")
            
            list_item_type = args_type[0]
            
            if list_item_type not in types_map:
                raise TypeError(f"Parameter '{name}': list[{list_item_type.__name__}] is not supported. Supported types: int, float, str, bool")
            
            if not default or not isinstance(default, list):
                raise TypeError(f"Parameter '{name}' with type list[{list_item_type.__name__}] must have a default value with options")
            
            if not all(isinstance(item, list_item_type) for item in default):
                raise TypeError(f"Parameter '{name}': all values in the default list must be of type {list_item_type.__name__}")
            
            if len(default) == 0:
                raise TypeError(f"Parameter '{name}': list[{list_item_type.__name__}] must have at least one option in the default value")
            
            params[name] = (real_type, default, None)
            continue
        
        # Variable para guardar metadata extra
        ui_metadata = {}
        
        if not args_type:
            try:
                ui_type = types_map[real_type]()
            except KeyError:
                raise TypeError(f"Unsupported type: {real_type}")
        else:
            base_type = args_type[0]
            
            # Detectar ColorUi PRIMERO antes de procesar constraints
            ui_type_override = None
            for c in args_type[1].metadata:
                if hasattr(c, 'json_schema_extra') and c.json_schema_extra and 'ui_type' in c.json_schema_extra:
                    ui_type_override = c.json_schema_extra['ui_type']
                    break
            
            if ui_type_override == 'color':
                ui_type = ColorUi()
                ui_metadata['is_color'] = True  # Marcar explícitamente como color
            else:
                # Solo aplicar constraints si NO es ColorUi
                constraints = {}
                for c in args_type[1].metadata:
                    if hasattr(c, 'ge'): constraints['min'] = c.ge
                    if hasattr(c, 'le'): constraints['max'] = c.le
                    if hasattr(c, 'min_length'): constraints['min_length'] = c.min_length
                    if hasattr(c, 'max_length'): constraints['max_length'] = c.max_length
                
                ui_type = types_map[base_type](**constraints)

        if default is not None:
            TypeAdapter(ui_type).validate_python(default)

        # Retornar ui_type + metadata extra
        params[name] = (ui_type, default, ui_metadata)

    return params