import inspect
from dataclasses import dataclass
from typing import Annotated, Literal, get_args, get_origin
import types

from pydantic import TypeAdapter
from datetime import date, time

from .types import _OptionalEnabledMarker, _OptionalDisabledMarker

VALID = {int, float, str, bool, date, time}

@dataclass
class ParamInfo:
    """
    Metadata about a function parameter extracted by analyze().
    
    This dataclass stores all the information needed to generate form fields,
    validate input, and call the function with the correct parameters.
    
    Attributes:
        type (type): The base Python type of the parameter. Must be one of:
            int, float, str, bool, date, or time.
            Example: int, str, date
            
        default (Any, optional): The default value specified in the parameter.
            - None if the parameter has no default
            - The actual default value if specified (e.g., 42, "hello", True)
            - Independent of is_optional (a parameter can be optional with or without a default)
            Example: For `age: int = 25`, default is 25
            Example: For `name: str`, default is None
            
        field_info (Any, optional): Additional metadata from Pydantic Field or Literal.
            - For Annotated types: Contains the Field object with constraints
              (e.g., Field(ge=0, le=100) for numeric bounds, Field(min_length=3) for strings)
            - For Literal types: Contains the Literal type with valid options
            - None for basic types without constraints
            Example: Field(ge=18, le=100) for age constraints
            Example: Literal['light', 'dark'] for dropdown options
            
        dynamic_func (callable, optional): Function for dynamic Literal options.
            - Only set for Literal[callable] type hints
            - Called at runtime to generate dropdown options dynamically
            - Returns a list, tuple, or single value
            - None for static Literals or non-Literal types
            Example: A function that returns database options
            
        is_optional (bool): Whether the parameter type includes None.
            - True for Type | None or Union[Type, None] syntax
            - False for regular required parameters (even if they have a default)
            - Affects UI: optional fields get a toggle switch to enable/disable
            - Default: False
            Example: `name: str | None` has is_optional=True
            Example: `age: int = 25` has is_optional=False (even with default)
            
        optional_enabled (bool): Initial state of optional toggle.
            - Only relevant when is_optional=True
            - True: toggle starts enabled (field active)
            - False: toggle starts disabled (field inactive, sends None)
            - Determined by: explicit marker > default value > False
            - Default: False
            Example: `name: str | OptionalEnabled` starts enabled
            Example: `name: str | OptionalDisabled` starts disabled
            Example: `name: str | None = "John"` starts enabled (has default)
            Example: `name: str | None` starts disabled (no default)
    
    """
    type: type
    default: any = None
    field_info: any = None
    dynamic_func: any = None
    is_optional: bool = False
    optional_enabled: bool = False

def analyze(func):
    """
    Analyze a function's signature and extract parameter metadata.
    
    Args:
        func: The function to analyze
        
    Returns:
        dict: Mapping of parameter names to ParamInfo objects
        
    Raises:
        TypeError: If parameter type is not supported
        ValueError: If default value doesn't match Literal options
        ValueError: If Literal options are invalid
        ValueError: If Union has multiple non-None types
        ValueError: If default value type doesn't match parameter type
    """
    from .types import _OptionalEnabledMarker, _OptionalDisabledMarker
    
    result = {}
    
    for name, p in inspect.signature(func).parameters.items():
        default = None if p.default == inspect.Parameter.empty else p.default
        t = p.annotation
        f = None
        dynamic_func = None
        is_optional = False
        optional_default_enabled = None  # None = auto, True = enabled, False = disabled
        
        # Extract base type from Annotated
        if get_origin(t) is Annotated:
            args = get_args(t)
            t = args[0]
            if len(args) > 1:
                f = args[1]
        
        # Check for Union types (including | None syntax)
        if get_origin(t) is types.UnionType or str(get_origin(t)) == 'typing.Union':
            union_args = get_args(t)
            
            # First pass: detect markers and check for None
            has_none = type(None) in union_args
            
            for arg in union_args:
                if get_origin(arg) is Annotated:
                    annotated_args = get_args(arg)
                    # Check if this is Annotated[None, Marker]
                    if annotated_args[0] is type(None) and len(annotated_args) > 1:
                        for marker in annotated_args[1:]:
                            if isinstance(marker, _OptionalEnabledMarker):
                                optional_default_enabled = True
                                is_optional = True
                            elif isinstance(marker, _OptionalDisabledMarker):
                                optional_default_enabled = False
                                is_optional = True
            
            # Second pass: extract the actual type (not None, not markers)
            if has_none or is_optional:
                is_optional = True
                non_none_types = []
                
                for arg in union_args:
                    # Skip plain None
                    if arg is type(None):
                        continue
                    
                    # Skip Annotated[None, Marker] (the markers)
                    if get_origin(arg) is Annotated:
                        annotated_args = get_args(arg)
                        if annotated_args[0] is type(None):
                            continue
                    
                    # This is the actual type
                    non_none_types.append(arg)
                
                if len(non_none_types) == 0:
                    raise TypeError(f"'{name}': Cannot have only None type")
                elif len(non_none_types) > 1:
                    raise TypeError(f"'{name}': Union with multiple non-None types not supported")
                
                # Extract the actual type
                t = non_none_types[0]
                
                # Check again if this is Annotated (for Field constraints)
                if get_origin(t) is Annotated:
                    args = get_args(t)
                    t = args[0]
                    if len(args) > 1 and f is None:
                        f = args[1]
        
        # Handle Literal types (dropdowns)
        if get_origin(t) is Literal:
            opts = get_args(t)
            
            # Check if opts contains a single callable (dynamic Literal)
            if len(opts) == 1 and callable(opts[0]):
                dynamic_func = opts[0]
                result_value = dynamic_func()
                
                # Convert result to tuple properly
                if isinstance(result_value, (list, tuple)):
                    opts = tuple(result_value)
                else:
                    opts = (result_value,)
            
            # Validate options
            if opts:
                types_set = {type(o) for o in opts}
                if len(types_set) > 1:
                    raise TypeError(f"'{name}': mixed types in Literal")
                if default is not None and default not in opts:
                    raise ValueError(f"'{name}': default '{default}' not in options {opts}")
                
                f = Literal[opts] if len(opts) > 0 else t
                t = types_set.pop() if types_set else type(None)
            else:
                t = type(None)
        
        if t not in VALID:
            raise TypeError(f"'{name}': {t} not supported")
        
        # Validate default value type matches parameter type
        if default is not None and not is_optional and get_origin(f) is not Literal:
            if not isinstance(default, t):
                raise TypeError(f"'{name}': default value type mismatch")
        
        # Validate default value against field constraints
        if f and default is not None and hasattr(f, 'metadata'):
            TypeAdapter(Annotated[t, f]).validate_python(default)
        
        # Determine optional_enabled state
        # Priority: explicit marker > default value presence > False
        if optional_default_enabled is not None:
            # Explicit marker takes priority
            final_optional_enabled = optional_default_enabled
        elif default is not None:
            # Has default value, start enabled
            final_optional_enabled = True
        else:
            # No default, start disabled
            final_optional_enabled = False
        
        result[name] = ParamInfo(t, default, f, dynamic_func, is_optional, final_optional_enabled)
    
    return result