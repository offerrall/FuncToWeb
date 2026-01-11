import inspect
from dataclasses import dataclass
from typing import Annotated, Literal, get_args, get_origin, Callable, Any
from enum import Enum
import types

from pydantic import TypeAdapter
from datetime import date, time

from .types import _OptionalEnabledMarker, _OptionalDisabledMarker, Dropdown

VALID = {int, float, str, bool, date, time}

@dataclass
class ParamInfo:
    """Metadata about a function parameter extracted by analyze().
    
    This dataclass stores all the information needed to generate form fields,
    validate input, and call the function with the correct parameters.
    
    Attributes:
        type: The base Python type of the parameter. Must be one of:
            int, float, str, bool, date, or time.
            Example: int, str, date
        default: The default value specified in the parameter.
            - None if the parameter has no default
            - The actual default value if specified (e.g., 42, "hello", True)
            - Independent of is_optional (a parameter can be optional with or without a default)
            Example: For `age: int = 25`, default is 25
            Example: For `name: str`, default is None
        field_info: Additional metadata from Pydantic Field or Literal.
            - For Annotated types: Contains the Field object with constraints
              (e.g., Field(ge=0, le=100) for numeric bounds, Field(min_length=3) for strings)
            - For Literal types: Contains the Literal type with valid options
            - None for basic types without constraints
            Example: Field(ge=18, le=100) for age constraints
            Example: Literal['light', 'dark'] for dropdown options
        dynamic_func: Function for dynamic Literal options.
            - Only set for Literal[callable] type hints
            - Called at runtime to generate dropdown options dynamically
            - Returns a list, tuple, or single value
            - None for static Literals or non-Literal types
            Example: A function that returns database options
        is_optional: Whether the parameter type includes None.
            - True for Type | None or Union[Type, None] syntax
            - False for regular required parameters (even if they have a default)
            - Affects UI: optional fields get a toggle switch to enable/disable
            - Default: False
            Example: `name: str | None` has is_optional=True
            Example: `age: int = 25` has is_optional=False (even with default)
        optional_enabled: Initial state of optional toggle.
            - Only relevant when is_optional=True
            - True: toggle starts enabled (field active)
            - False: toggle starts disabled (field inactive, sends None)
            - Determined by: explicit marker > default value > False
            - Default: False
            Example: `name: str | OptionalEnabled` starts enabled
            Example: `name: str | OptionalDisabled` starts disabled
            Example: `name: str | None = "John"` starts enabled (has default)
            Example: `name: str | None` starts disabled (no default)
        is_list: Whether the parameter is a list type.
            - True for list[Type] syntax
            - False for regular parameters
            - When True, 'type' contains the item type, not list
            - Default: False
        list_field_info: Metadata for the list itself (min_items, max_items).
            - Only relevant when is_list=True
            - Contains Field constraints for the list container
            - None if no list-level constraints
            Example: Field(min_items=2, max_items=5)
        enum_type: The original Enum type if parameter was an Enum.
            - None for non-Enum parameters
            - Stored to convert string back to Enum in validation
            - Example: For `color: Color`, stores the Color Enum class
    """
    type: type
    default: Any = None
    field_info: Any = None
    dynamic_func: Any = None
    is_optional: bool = False
    optional_enabled: bool = False
    is_list: bool = False
    list_field_info: Any = None
    enum_type: None = None

def analyze(func: Callable[..., Any]) -> dict[str, ParamInfo]:
    """Analyze a function's signature and extract parameter metadata.
    
    Args:
        func: The function to analyze.
        
    Returns:
        Mapping of parameter names to ParamInfo objects.
        
    Raises:
        TypeError: If parameter type is not supported.
        TypeError: If list has no type parameter.
        TypeError: If list item type is not supported.
        TypeError: If list of Literal is used (conceptually confusing).
        TypeError: If list default is not a list.
        TypeError: If list default items have wrong type.
        ValueError: If default value doesn't match Literal options.
        ValueError: If Literal options are invalid.
        ValueError: If Union has multiple non-None types.
        ValueError: If default value type doesn't match parameter type.
    """
    
    result = {}
    
    for name, p in inspect.signature(func).parameters.items():
        default = None if p.default == inspect.Parameter.empty else p.default
        t = p.annotation
        f = None
        list_f = None  # Field info for the list itself
        dynamic_func = None
        is_optional = False
        optional_default_enabled = None  # None = auto, True = enabled, False = disabled
        is_list = False
        enum_type = None
        
        # 1. Extract base type from Annotated (OUTER level)
        # This could be constraints for the list itself
        if get_origin(t) is Annotated:
            args = get_args(t)
            t = args[0]
            if len(args) > 1:
                # Store this temporarily - we'll decide if it's for list or item later
                list_f = args[1]
        
        # 2. Check for Union types (including | None syntax) BEFORE list detection
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
                    if len(args) > 1 and list_f is None:
                        list_f = args[1]
        
        # 3. Detect list type
        if get_origin(t) is list:
            is_list = True
            list_args = get_args(t)
            
            if not list_args:
                raise TypeError(f"'{name}': list must have type parameter (e.g., list[int])")
            
            # Extract item type
            t = list_args[0]
            
            # Check if item type is Literal (before extracting Annotated)
            if get_origin(t) is Literal:
                raise TypeError(f"'{name}': list of Literal not supported")
            
            # 4. Extract Annotated from ITEM type
            if get_origin(t) is Annotated:
                args = get_args(t)
                t = args[0]
                
                # Check again for Literal after extracting Annotated
                if get_origin(t) is Literal:
                    raise TypeError(f"'{name}': list of Literal not supported")
                
                if len(args) > 1:
                    f = args[1]  # Field constraints for EACH ITEM
        elif t is list:
            # Handle bare 'list' without type parameter
            raise TypeError(f"'{name}': list must have type parameter (e.g., list[int])")
        
        # If not a list, then list_f is actually the field_info for the item
        if not is_list and list_f is not None:
            f = list_f
            list_f = None
        
        # 4.5 Detect and process Dropdown
        dropdown_instance = None
        
        # Check if Dropdown is in metadata
        if f and isinstance(f, Dropdown):
            dropdown_instance = f
            f = None
        elif list_f and isinstance(list_f, Dropdown):
            dropdown_instance = list_f
            list_f = None
        
        # Process Dropdown if found
        if dropdown_instance:
            # Execute function to get options
            opts = dropdown_instance.data_function()
            
            # Validate it's a list
            if not isinstance(opts, list):
                raise TypeError(f"'{name}': Dropdown function must return a list, got {type(opts).__name__}")
            
            if not opts:
                raise ValueError(f"'{name}': Dropdown function returned empty list")
            
            # Validate all options are same type
            types_set = {type(o) for o in opts}
            if len(types_set) > 1:
                raise TypeError(f"'{name}': Dropdown returned mixed types")
            
            # Validate returned type matches declared type
            returned_type = types_set.pop()
            if returned_type != t:
                raise TypeError(
                    f"'{name}': Dropdown type mismatch. "
                    f"Declared type is {t.__name__}, but function returned {returned_type.__name__}"
                )
            
            # Validate default against options
            if not is_list and default is not None and default not in opts:
                raise ValueError(f"'{name}': default '{default}' not in Dropdown options {opts}")
            
            # Convert to Literal for rest of pipeline
            f = Literal[tuple(opts)]
            dynamic_func = dropdown_instance.data_function
        
        # 5. Handle Literal types (dropdowns)
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
                
                # For lists, we can't validate default against Literal here (it's a list)
                if not is_list and default is not None and default not in opts:
                    raise ValueError(f"'{name}': default '{default}' not in options {opts}")
                
                f = Literal[opts] if len(opts) > 0 else t
                t = types_set.pop() if types_set else type(None)
            else:
                t = type(None)
        
        # 5b. Handle Enum types
        elif isinstance(t, type) and issubclass(t, Enum):
            opts = tuple(e.value for e in t)

            if not opts:
                raise ValueError(f"'{name}': Enum must have at least one value")

            types_set = {type(v) for v in opts}
            if len(types_set) > 1:
                raise TypeError(f"'{name}': Enum values must be same type")

            if default is not None:
                if not isinstance(default, t):
                    raise TypeError(f"'{name}': default must be {t.__name__} instance")
                default = default.value
            
            enum_type = t
            
            f = Literal[opts]
            t = types_set.pop()
        
        # 6. Validate base type
        if t not in VALID:
            raise TypeError(f"'{name}': {t} not supported")
        
        # 7. Validate default value
        if default is not None:
            if is_list:
                # Must be a list
                if not isinstance(default, list):
                    raise TypeError(f"'{name}': default must be a list")
                
                # Validate list-level constraints BEFORE converting empty list to None
                if list_f and hasattr(list_f, 'metadata'):
                    TypeAdapter(Annotated[list[t], list_f]).validate_python(default)
                
                # Validate each item
                for item in default:
                    # Check type
                    if not isinstance(item, t):
                        raise TypeError(f"'{name}': list item type mismatch in default")
                    
                    # Validate against Field constraints (for items)
                    if f and hasattr(f, 'metadata'):
                        TypeAdapter(Annotated[t, f]).validate_python(item)
                
                # Convert empty list to None AFTER validation
                if len(default) == 0:
                    default = None
            else:
                # Non-list validation (existing logic)
                if not is_optional and get_origin(f) is not Literal:
                    if not isinstance(default, t):
                        raise TypeError(f"'{name}': default value type mismatch")
                
                # Validate default value against field constraints
                if f and hasattr(f, 'metadata'):
                    TypeAdapter(Annotated[t, f]).validate_python(default)
        
        # 8. Determine optional_enabled state
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
        
        result[name] = ParamInfo(t, default, f, dynamic_func, is_optional, final_optional_enabled, is_list, list_f, enum_type)
    
    return result