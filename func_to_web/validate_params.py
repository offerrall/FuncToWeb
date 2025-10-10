from datetime import date, time
from typing import Annotated, Literal, get_args, get_origin
from pydantic import TypeAdapter

from .analyze_function import ParamInfo


def validate_params(form_data, params_info):
    """
    Validate and convert form data to function parameters.
    
    This function takes raw form data (where everything is a string) and converts
    it to the proper Python types based on the parameter metadata from analyze().
    It handles type conversion, optional field toggles, and validates against
    constraints defined in Pydantic Field or Literal types.
    
    Process:
        1. Check if optional fields are enabled via toggle
        2. Convert strings to proper types (int, float, date, time, bool)
        3. Validate Literal values against allowed options
        4. Validate against Pydantic Field constraints (ge, le, min_length, etc.)
        5. Handle special cases (hex color expansion, empty values)
    
    Args:
        form_data (dict): Raw form data from HTTP request.
            - Keys are parameter names (str)
            - Values are form values (str, or None for checkboxes)
            - Optional toggles have keys like "{param}_optional_toggle"
            
        params_info (dict): Parameter metadata from analyze().
            - Keys are parameter names (str)
            - Values are ParamInfo objects with type and validation info
    
    Returns:
        dict: Validated parameters ready for function call.
            - Keys are parameter names (str)
            - Values are properly typed Python objects
            
    Raises:
        ValueError: If a value doesn't match Literal options or Field constraints
        TypeError: If type conversion fails
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