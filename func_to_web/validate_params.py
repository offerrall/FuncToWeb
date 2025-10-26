from datetime import date, time
from typing import Annotated, Literal, get_args, get_origin, Any
from pydantic import TypeAdapter
import json

from .analyze_function import ParamInfo


def validate_params(form_data: dict, params_info: dict[str, ParamInfo]) -> dict:
    """Validate and convert form data to function parameters.
    
    This function takes raw form data (where everything is a string) and converts
    it to the proper Python types based on the parameter metadata from analyze().
    It handles type conversion, optional field toggles, and validates against
    constraints defined in Pydantic Field or Literal types.
    
    Process:
        1. Check if optional fields are enabled via toggle
        2. Convert strings to proper types (int, float, date, time, bool)
        3. For lists: parse JSON and validate each item
        4. Validate Literal values against allowed options
        5. Validate against Pydantic Field constraints (ge, le, min_length, etc.)
        6. Handle special cases (hex color expansion, empty values)
    
    Args:
        form_data: Raw form data from HTTP request.
            - Keys are parameter names (str)
            - Values are form values (str, or None for checkboxes)
            - For lists: JSON string like "[1, 2, 3]"
            - Optional toggles have keys like "{param}_optional_toggle"
        params_info: Parameter metadata from analyze().
            - Keys are parameter names (str)
            - Values are ParamInfo objects with type and validation info
    
    Returns:
        Validated parameters ready for function call.
        Keys are parameter names (str), values are properly typed Python objects.
            
    Raises:
        ValueError: If a value doesn't match Literal options or Field constraints.
        TypeError: If type conversion fails.
        json.JSONDecodeError: If list JSON is invalid.
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
        
        # Handle list fields
        if info.is_list:
            validated[name] = validate_list_param(value, info, name)
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


def validate_list_param(value: str | None, info: ParamInfo, param_name: str) -> list:
    """Validate and convert a JSON string to a typed list.
    
    Args:
        value: JSON string like "[1, 2, 3]" or "[]".
        info: ParamInfo with type and constraints for list items.
        param_name: Name of the parameter (for error messages).
    
    Returns:
        Validated list with proper types.
        
    Raises:
        TypeError: If value is not a valid list.
        ValueError: If items don't pass validation or list size constraints are violated.
        json.JSONDecodeError: If JSON is invalid.
    """
    # Parse JSON
    if not value or value == "":
        list_value = []
    else:
        try:
            list_value = json.loads(value)
        except json.JSONDecodeError as e:
            raise ValueError(f"'{param_name}': Invalid list format: {e}")
    
    if not isinstance(list_value, list):
        raise TypeError(f"'{param_name}': Expected list, got {type(list_value).__name__}")
    
    # Validate list-level constraints (min_length, max_length)
    if info.list_field_info and hasattr(info.list_field_info, 'metadata'):
        min_length = None
        max_length = None
        
        for constraint in info.list_field_info.metadata:
            constraint_name = type(constraint).__name__
            
            # Pydantic usa 'MinLen' y 'MaxLen' para constraints de longitud
            if constraint_name == 'MinLen':
                min_length = constraint.min_length
            elif constraint_name == 'MaxLen':
                max_length = constraint.max_length
            # También buscar por el atributo directamente
            elif hasattr(constraint, 'min_length'):
                min_length = constraint.min_length
            elif hasattr(constraint, 'max_length'):
                max_length = constraint.max_length
        
        # Validate min_length
        if min_length is not None and len(list_value) < min_length:
            raise ValueError(
                f"'{param_name}': List must have at least {min_length} item{'s' if min_length != 1 else ''}, "
                f"got {len(list_value)}"
            )
        
        # Validate max_length
        if max_length is not None and len(list_value) > max_length:
            raise ValueError(
                f"'{param_name}': List must have at most {max_length} item{'s' if max_length != 1 else ''}, "
                f"got {len(list_value)}"
            )
    
    # Validate each item
    validated_list = []
    for i, item in enumerate(list_value):
        try:
            validated_item = validate_single_item(item, info)
            validated_list.append(validated_item)
        except (ValueError, TypeError) as e:
            raise ValueError(f"'{param_name}': List item at index {i}: {e}")
    
    return validated_list


def validate_single_item(item: Any, info: ParamInfo) -> Any:
    """Validate a single list item.
    
    Reuses the same validation logic as non-list parameters.
    
    Args:
        item: The item value from the JSON array.
        info: ParamInfo with type and constraints.
    
    Returns:
        Validated and converted item.
    """
    # Handle None/null values
    if item is None:
        return None
    
    # Bool (already bool from JSON)
    if info.type is bool:
        return bool(item)
    
    # Date (comes as string from JSON)
    if info.type is date:
        if isinstance(item, str):
            return date.fromisoformat(item)
        return item
    
    # Time (comes as string from JSON)
    if info.type is time:
        if isinstance(item, str):
            return time.fromisoformat(item)
        return item
    
    # Literal in lists is not supported (prohibited by analyze())
    if get_origin(info.field_info) is Literal:
        raise TypeError("list[Literal[...]] is not supported")
    
    # Expand shorthand hex colors (#RGB -> #RRGGBB)
    if item and isinstance(item, str) and item.startswith('#') and len(item) == 4:
        item = '#' + ''.join(c*2 for c in item[1:])
    
    # Number types: ensure conversion from string if needed
    if info.type in (int, float):
        if isinstance(item, str):
            item = info.type(item)
        elif isinstance(item, (int, float)):
            # JSON already parsed it as number
            item = info.type(item)
    
    # Pydantic validation with constraints
    if info.field_info and hasattr(info.field_info, 'metadata'):
        adapter = TypeAdapter(Annotated[info.type, info.field_info])
        return adapter.validate_python(item)
    else:
        # Basic type conversion for types without constraints
        if info.type in (int, float):
            # Already converted above
            return item
        elif info.type is str:
            return str(item) if item is not None else None
        else:
            # For other types (shouldn't reach here normally)
            return info.type(item) if item is not None else None