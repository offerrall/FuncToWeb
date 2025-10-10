import inspect
from dataclasses import dataclass
from typing import Annotated, Literal, get_args, get_origin
import types

from pydantic import TypeAdapter
from datetime import date, time

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
            
        default (Any, optional): The default value specified in the function signature.
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
    
    """
    type: type
    default: any = None
    field_info: any = None
    dynamic_func: any = None
    is_optional: bool = False

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
    result = {}
    
    for name, p in inspect.signature(func).parameters.items():
        default = None if p.default == inspect.Parameter.empty else p.default
        t = p.annotation
        f = None
        dynamic_func = None
        is_optional = False
        
        # Extract base type from Annotated
        if get_origin(t) is Annotated:
            args = get_args(t)
            t = args[0]
            if len(args) > 1:
                f = args[1]
        
        # Check for Union types (including | None syntax)
        if get_origin(t) is types.UnionType or str(get_origin(t)) == 'typing.Union':
            union_args = get_args(t)
            
            # Check if None is in the union (making it optional)
            if type(None) in union_args:
                is_optional = True
                # Remove None from the types and get the actual type
                non_none_types = [arg for arg in union_args if arg is not type(None)]
                
                if len(non_none_types) == 0:
                    raise TypeError(f"'{name}': Cannot have only None type")
                elif len(non_none_types) > 1:
                    raise TypeError(f"'{name}': Union with multiple non-None types not supported")
                
                # Extract the actual type
                t = non_none_types[0]
                
                # Check again if this is Annotated
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
        
        result[name] = ParamInfo(t, default, f, dynamic_func, is_optional)
    
    return result