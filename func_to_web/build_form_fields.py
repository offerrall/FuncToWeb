from datetime import date, time
from typing import Literal, get_args, get_origin

from .types import COLOR_PATTERN, EMAIL_PATTERN

PATTERN_TO_HTML_TYPE = {COLOR_PATTERN: 'color', EMAIL_PATTERN: 'email'}

def build_form_fields(params_info):
    """
    Build form field specifications from parameter metadata.
    Re-executes dynamic functions to get fresh options.
    
    This function takes the analyzed parameter information from analyze() and
    converts it into a list of field specifications that can be used by the
    template engine to generate HTML form inputs.
    
    Process:
        1. Iterate through each parameter's ParamInfo
        2. Determine the appropriate HTML input type (text, number, select, etc.)
        3. Extract constraints and convert them to HTML attributes
        4. Handle special cases (optional fields, dynamic literals, files, etc.)
        5. Return list of field dictionaries ready for template rendering
    
    Args:
        params_info (dict): Mapping of parameter names to ParamInfo objects.
            Keys are parameter names (str)
            Values are ParamInfo objects with type, default, field_info, etc.
            
    Returns:
        list: List of field dictionaries for template rendering.
            Each dictionary contains:
            - name (str): Parameter name
            - type (str): HTML input type ('text', 'number', 'select', etc.)
            - default (Any): Default value for the field
            - required (bool): Whether field is required
            - is_optional (bool): Whether field has optional toggle
            - optional_enabled (bool): Whether optional field starts enabled
            - options (tuple): For select fields, the dropdown options
            - min/max (int/float): For number fields, numeric constraints
            - minlength/maxlength (int): For text fields, length constraints
            - pattern (str): Regex pattern for validation
            - accept (str): For file fields, accepted file extensions
            - step (str): For number fields, '1' for int, 'any' for float
    
    Field Type Detection:
        - Literal types → 'select' (dropdown)
        - bool → 'checkbox'
        - date → 'date' (date picker)
        - time → 'time' (time picker)
        - int/float → 'number' (with constraints)
        - str with file pattern → 'file' (file upload)
        - str with color pattern → 'color' (color picker)
        - str with email pattern → 'email' (email input)
        - str (default) → 'text' (text input)

    """
    fields = []
    
    for name, info in params_info.items():
        field = {
            'name': name, 
            'default': info.default,
            'required': not info.is_optional,
            'is_optional': info.is_optional,
            'optional_enabled': info.default is not None
        }
        
        # Dropdown select
        if get_origin(info.field_info) is Literal:
            field['type'] = 'select'
            
            # Re-execute dynamic function if present
            if info.dynamic_func is not None:
                result_value = info.dynamic_func()
                
                # Convert result to tuple properly
                if isinstance(result_value, (list, tuple)):
                    fresh_options = tuple(result_value)
                else:
                    fresh_options = (result_value,)
                
                field['options'] = fresh_options
                info.field_info = Literal[fresh_options]
            else:
                field['options'] = get_args(info.field_info)
            
        # Checkbox
        elif info.type is bool:
            field['type'] = 'checkbox'
            field['required'] = False
            
        # Date picker
        elif info.type is date:
            field['type'] = 'date'
            if isinstance(info.default, date):
                field['default'] = info.default.isoformat()
        
        # Time picker
        elif info.type is time:
            field['type'] = 'time'
            if isinstance(info.default, time):
                field['default'] = info.default.strftime('%H:%M')
            
        # Number input
        elif info.type in (int, float):
            field['type'] = 'number'
            field['step'] = '1' if info.type is int else 'any'
            
            # Extract numeric constraints from Pydantic Field
            if info.field_info and hasattr(info.field_info, 'metadata'):
                for c in info.field_info.metadata:
                    cn = type(c).__name__
                    if cn == 'Ge': field['min'] = c.ge
                    elif cn == 'Le': field['max'] = c.le
                    elif cn == 'Gt': field['min'] = c.gt + (1 if info.type is int else 0.01)
                    elif cn == 'Lt': field['max'] = c.lt - (1 if info.type is int else 0.01)
                    
        # Text/email/color/file input
        else:
            field['type'] = 'text'
            
            if info.field_info and hasattr(info.field_info, 'metadata'):
                for c in info.field_info.metadata:
                    cn = type(c).__name__
                    
                    # Check for pattern constraints
                    if hasattr(c, 'pattern') and c.pattern:
                        pattern = c.pattern
                        
                        # File input detection
                        if pattern.startswith(r'^.+\.(') and pattern.endswith(r')$'):
                            field['type'] = 'file'
                            exts = pattern[6:-2].split('|')
                            field['accept'] = '.' + ',.'.join(exts)
                        # Special input types (color, email)
                        elif pattern in PATTERN_TO_HTML_TYPE:
                            field['type'] = PATTERN_TO_HTML_TYPE[pattern]
                        
                        field['pattern'] = pattern
                    
                    # String length constraints
                    if cn == 'MinLen': 
                        field['minlength'] = c.min_length
                    if cn == 'MaxLen':
                        field['maxlength'] = c.max_length
        
        fields.append(field)
    
    return fields