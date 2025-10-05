from typing import get_args, get_origin
from pydantic import TypeAdapter
import inspect

from .ui_types import *


def _process_list_type(name, annotation, default, types_map):
    """Procesa parámetros de tipo list[T]"""
    args_type = get_args(annotation)
    
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
    
    return annotation, default


def _process_annotated_type(annotation, types_map):
    """Procesa parámetros de tipo Annotated[T, ...]"""
    args_type = get_args(annotation)
    
    if not args_type:
        # Tipo simple sin Annotated (int, str, bool, float)
        try:
            return types_map[annotation]()
        except KeyError:
            raise TypeError(f"Unsupported type: {annotation}")
    
    base_type = args_type[0]
    constraints = {}
    
    # Extraer constraints del Field
    for c in args_type[1].metadata:
        if hasattr(c, 'ge'): constraints['min'] = c.ge
        if hasattr(c, 'le'): constraints['max'] = c.le
        if hasattr(c, 'min_length'): constraints['min_length'] = c.min_length
        if hasattr(c, 'max_length'): constraints['max_length'] = c.max_length
    
    return types_map[base_type](**constraints)


def analyze(func):
    """Analiza una función y extrae información de sus parámetros para generar UI"""
    types_map = {int: IntUi, float: FloatUi, str: StrUi, bool: BoolUi}
    sig = inspect.signature(func)
    params = {}

    for name, param in sig.parameters.items():
        annotation = func.__annotations__.get(name)
        
        if not annotation:
            raise TypeError("All parameters must have type hints.")

        default = param.default if param.default != inspect.Parameter.empty else None
        origin_type = get_origin(annotation)
        
        # Procesar list[T]
        if origin_type is list:
            ui_type, validated_default = _process_list_type(name, annotation, default, types_map)
            params[name] = (ui_type, validated_default)
            continue
        
        # Procesar Annotated[T, ...] o tipos simples
        ui_type = _process_annotated_type(annotation, types_map)
        
        # Validar default si existe
        if default is not None:
            TypeAdapter(ui_type).validate_python(default)
        
        params[name] = (ui_type, default)

    return params