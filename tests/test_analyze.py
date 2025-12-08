import pytest
from datetime import date, time
from pydantic import Field, ValidationError
from typing import Union
import math

from func_to_web import *
from func_to_web.types import *

# --- BASIC TYPES ---

def test_int_parameter():
    def func(x: int): 
        pass
    
    params = analyze(func)
    
    assert 'x' in params
    assert params['x'].type == int
    assert params['x'].default is None
    assert params['x'].field_info is None
    assert params['x'].dynamic_func is None
    assert params['x'].is_optional is False

def test_float_parameter():
    def func(price: float): 
        pass
    
    params = analyze(func)
    
    assert 'price' in params
    assert params['price'].type == float
    assert params['price'].default is None
    assert params['price'].field_info is None
    assert params['price'].dynamic_func is None
    assert params['price'].is_optional is False

def test_str_parameter():
    def func(name: str): 
        pass
    
    params = analyze(func)
    
    assert 'name' in params
    assert params['name'].type == str
    assert params['name'].default is None
    assert params['name'].field_info is None
    assert params['name'].dynamic_func is None
    assert params['name'].is_optional is False

def test_bool_parameter():
    def func(active: bool): 
        pass
    
    params = analyze(func)
    
    assert 'active' in params
    assert params['active'].type == bool
    assert params['active'].default is None
    assert params['active'].field_info is None
    assert params['active'].dynamic_func is None
    assert params['active'].is_optional is False

def test_date_parameter():
    def func(birthday: date): 
        pass
    
    params = analyze(func)
    
    assert 'birthday' in params
    assert params['birthday'].type == date
    assert params['birthday'].default is None
    assert params['birthday'].field_info is None
    assert params['birthday'].dynamic_func is None
    assert params['birthday'].is_optional is False

def test_time_parameter():
    def func(meeting: time): 
        pass
    
    params = analyze(func)
    
    assert 'meeting' in params
    assert params['meeting'].type == time
    assert params['meeting'].default is None
    assert params['meeting'].field_info is None
    assert params['meeting'].dynamic_func is None
    assert params['meeting'].is_optional is False

def test_dict_type_raises():
    with pytest.raises(TypeError, match="not supported"):
        def func(data: dict): 
            pass
        analyze(func)

def test_list_type_raises():
    with pytest.raises(TypeError, match="list must have type parameter"):
        def func(items: list): 
            pass
        analyze(func)

def test_set_type_raises():
    with pytest.raises(TypeError, match="not supported"):
        def func(items: set): 
            pass
        analyze(func)

def test_tuple_type_raises():
    with pytest.raises(TypeError, match="not supported"):
        def func(items: tuple): 
            pass
        analyze(func)

def test_custom_class_raises():
    class CustomClass: 
        pass
    
    with pytest.raises(TypeError, match="not supported"):
        def func(obj: CustomClass): 
            pass
        analyze(func)

def test_any_type_raises():
    from typing import Any
    
    with pytest.raises(TypeError, match="not supported"):
        def func(data: Any): 
            pass
        analyze(func)

def test_none_type_raises():
    with pytest.raises(TypeError, match="not supported"):
        def func(data: None): 
            pass
        analyze(func)

# --- BASIC TYPES WITH DEFAULTS ---

def test_int_with_default():
    def func(age: int = 25): 
        pass
    
    params = analyze(func)
    
    assert 'age' in params
    assert params['age'].type == int
    assert params['age'].default == 25
    assert params['age'].field_info is None
    assert params['age'].dynamic_func is None
    assert params['age'].is_optional is False

def test_str_with_default():
    def func(name: str = "John"): 
        pass
    
    params = analyze(func)
    
    assert 'name' in params
    assert params['name'].type == str
    assert params['name'].default == "John"
    assert params['name'].field_info is None
    assert params['name'].dynamic_func is None
    assert params['name'].is_optional is False

def test_bool_with_default():
    def func(active: bool = True): 
        pass
    
    params = analyze(func)
    
    assert 'active' in params
    assert params['active'].type == bool
    assert params['active'].default is True
    assert params['active'].field_info is None
    assert params['active'].dynamic_func is None
    assert params['active'].is_optional is False

def test_float_with_default():
    def func(price: float = 9.99): 
        pass
    
    params = analyze(func)
    
    assert 'price' in params
    assert params['price'].type == float
    assert params['price'].default == 9.99
    assert params['price'].field_info is None
    assert params['price'].dynamic_func is None
    assert params['price'].is_optional is False

def test_date_with_default():
    default_date = date(2000, 1, 1)
    
    def func(birthday: date = default_date): 
        pass
    
    params = analyze(func)
    
    assert 'birthday' in params
    assert params['birthday'].type == date
    assert params['birthday'].default == default_date
    assert params['birthday'].field_info is None
    assert params['birthday'].dynamic_func is None
    assert params['birthday'].is_optional is False

def test_time_with_default():
    default_time = time(14, 30)
    
    def func(meeting: time = default_time): 
        pass
    
    params = analyze(func)
    
    assert 'meeting' in params
    assert params['meeting'].type == time
    assert params['meeting'].default == default_time
    assert params['meeting'].field_info is None
    assert params['meeting'].dynamic_func is None
    assert params['meeting'].is_optional is False

def test_int_with_str_default_raises():
    with pytest.raises((TypeError, ValueError)):
        def func(age: int = "twenty"): 
            pass
        analyze(func)

def test_float_with_str_default_raises():
    with pytest.raises((TypeError, ValueError)):
        def func(price: float = "nine"): 
            pass
        analyze(func)

def test_bool_with_int_default_raises():
    with pytest.raises((TypeError, ValueError)):
        def func(active: bool = 1): 
            pass
        analyze(func)

def test_date_with_str_default_raises():
    with pytest.raises((TypeError, ValueError)):
        def func(birthday: date = "2000-01-01"): 
            pass
        analyze(func)

def test_time_with_str_default_raises():
    with pytest.raises((TypeError, ValueError)):
        def func(meeting: time = "14:30"): 
            pass
        analyze(func)

def test_str_with_int_default_raises():
    with pytest.raises((TypeError, ValueError)):
        def func(name: str = 123): 
            pass
        analyze(func)

# --- ANNOTATED TYPES WITH CONSTRAINTS ---

def test_int_with_constraints():
    def func(age: Annotated[int, Field(ge=0, le=120)]): 
        pass
    
    params = analyze(func)
    
    assert 'age' in params
    assert params['age'].type == int
    assert params['age'].default is None
    assert params['age'].field_info is not None
    assert params['age'].dynamic_func is None
    assert params['age'].is_optional is False

def test_int_with_ge_only():
    def func(age: Annotated[int, Field(ge=18)]): 
        pass
    
    params = analyze(func)
    
    assert 'age' in params
    assert params['age'].type == int
    assert params['age'].default is None
    assert params['age'].field_info is not None
    assert params['age'].dynamic_func is None
    assert params['age'].is_optional is False

def test_int_with_le_only():
    def func(age: Annotated[int, Field(le=100)]): 
        pass
    
    params = analyze(func)
    
    assert 'age' in params
    assert params['age'].type == int
    assert params['age'].default is None
    assert params['age'].field_info is not None
    assert params['age'].dynamic_func is None
    assert params['age'].is_optional is False

def test_float_with_gt_lt():
    def func(rating: Annotated[float, Field(gt=0, lt=5)]): 
        pass
    
    params = analyze(func)
    
    assert 'rating' in params
    assert params['rating'].type == float
    assert params['rating'].default is None
    assert params['rating'].field_info is not None
    assert params['rating'].dynamic_func is None
    assert params['rating'].is_optional is False

def test_str_with_length_constraints():
    def func(username: Annotated[str, Field(min_length=3, max_length=20)]): 
        pass
    
    params = analyze(func)
    
    assert 'username' in params
    assert params['username'].type == str
    assert params['username'].default is None
    assert params['username'].field_info is not None
    assert params['username'].dynamic_func is None
    assert params['username'].is_optional is False

def test_str_with_min_length_only():
    def func(password: Annotated[str, Field(min_length=8)]): 
        pass
    
    params = analyze(func)
    
    assert 'password' in params
    assert params['password'].type == str
    assert params['password'].default is None
    assert params['password'].field_info is not None
    assert params['password'].dynamic_func is None
    assert params['password'].is_optional is False

def test_str_with_max_length_only():
    def func(bio: Annotated[str, Field(max_length=500)]): 
        pass
    
    params = analyze(func)
    
    assert 'bio' in params
    assert params['bio'].type == str
    assert params['bio'].default is None
    assert params['bio'].field_info is not None
    assert params['bio'].dynamic_func is None
    assert params['bio'].is_optional is False

# --- ANNOTATED TYPES WITH DEFAULTS ---

def test_annotated_with_default():
    def func(age: Annotated[int, Field(ge=0, le=120)] = 25): 
        pass
    
    params = analyze(func)
    
    assert 'age' in params
    assert params['age'].type == int
    assert params['age'].default == 25
    assert params['age'].field_info is not None
    assert params['age'].dynamic_func is None
    assert params['age'].is_optional is False

def test_annotated_str_with_default():
    def func(username: Annotated[str, Field(min_length=3, max_length=20)] = "john"): 
        pass
    
    params = analyze(func)
    
    assert 'username' in params
    assert params['username'].type == str
    assert params['username'].default == "john"
    assert params['username'].field_info is not None
    assert params['username'].dynamic_func is None
    assert params['username'].is_optional is False

def test_annotated_int_default_below_minimum_raises():
    with pytest.raises(ValueError):
        def func(age: Annotated[int, Field(ge=18)] = 10): 
            pass
        analyze(func)

def test_annotated_int_default_above_maximum_raises():
    with pytest.raises(ValueError):
        def func(age: Annotated[int, Field(le=100)] = 150): 
            pass
        analyze(func)

def test_annotated_str_default_too_short_raises():
    with pytest.raises(ValueError):
        def func(username: Annotated[str, Field(min_length=5)] = "ab"): 
            pass
        analyze(func)

def test_annotated_str_default_too_long_raises():
    with pytest.raises(ValueError):
        def func(bio: Annotated[str, Field(max_length=10)] = "a" * 20): 
            pass
        analyze(func)

def test_annotated_float_default_below_gt_raises():
    with pytest.raises(ValueError):
        def func(rating: Annotated[float, Field(gt=0)] = 0.0): 
            pass
        analyze(func)

def test_annotated_float_default_above_lt_raises():
    with pytest.raises(ValueError):
        def func(rating: Annotated[float, Field(lt=5)] = 5.0): 
            pass
        analyze(func)

# --- SPECIAL TYPES ---

def test_color_type():
    def func(color: Color): 
        pass
    
    params = analyze(func)
    
    assert 'color' in params
    assert params['color'].type == str
    assert params['color'].default is None
    assert params['color'].field_info is not None
    assert params['color'].dynamic_func is None
    assert params['color'].is_optional is False

def test_color_with_default():
    def func(color: Color = "#ff0000"): 
        pass
    
    params = analyze(func)
    
    assert 'color' in params
    assert params['color'].type == str
    assert params['color'].default == "#ff0000"
    assert params['color'].field_info is not None
    assert params['color'].dynamic_func is None
    assert params['color'].is_optional is False

def test_email_type():
    def func(email: Email): 
        pass
    
    params = analyze(func)
    
    assert 'email' in params
    assert params['email'].type == str
    assert params['email'].default is None
    assert params['email'].field_info is not None
    assert params['email'].dynamic_func is None
    assert params['email'].is_optional is False

def test_email_with_default():
    def func(email: Email = "test@example.com"): 
        pass
    
    params = analyze(func)
    
    assert 'email' in params
    assert params['email'].type == str
    assert params['email'].default == "test@example.com"
    assert params['email'].field_info is not None
    assert params['email'].dynamic_func is None
    assert params['email'].is_optional is False

def test_image_file_type():
    def func(photo: ImageFile): 
        pass
    
    params = analyze(func)
    
    assert 'photo' in params
    assert params['photo'].type == str
    assert params['photo'].default is None
    assert params['photo'].field_info is not None
    assert params['photo'].dynamic_func is None
    assert params['photo'].is_optional is False

def test_data_file_type():
    def func(data: DataFile): 
        pass
    
    params = analyze(func)
    
    assert 'data' in params
    assert params['data'].type == str
    assert params['data'].default is None
    assert params['data'].field_info is not None
    assert params['data'].dynamic_func is None
    assert params['data'].is_optional is False

def test_text_file_type():
    def func(notes: TextFile): 
        pass
    
    params = analyze(func)
    
    assert 'notes' in params
    assert params['notes'].type == str
    assert params['notes'].default is None
    assert params['notes'].field_info is not None
    assert params['notes'].dynamic_func is None
    assert params['notes'].is_optional is False

def test_document_file_type():
    def func(report: DocumentFile): 
        pass
    
    params = analyze(func)
    
    assert 'report' in params
    assert params['report'].type == str
    assert params['report'].default is None
    assert params['report'].field_info is not None
    assert params['report'].dynamic_func is None
    assert params['report'].is_optional is False

def test_color_with_invalid_default_raises():
    with pytest.raises(ValueError):
        def func(color: Color = "red"): 
            pass
        analyze(func)

def test_color_with_invalid_hex_default_raises():
    with pytest.raises(ValueError):
        def func(color: Color = "#gggggg"): 
            pass
        analyze(func)

def test_email_with_invalid_default_raises():
    with pytest.raises(ValueError):
        def func(email: Email = "notanemail"): 
            pass
        analyze(func)

def test_email_with_invalid_format_raises():
    with pytest.raises(ValueError):
        def func(email: Email = "@example.com"): 
            pass
        analyze(func)

# --- LITERAL TYPES ---

def test_literal_string():
    def func(theme: Literal['light', 'dark', 'auto']): 
        pass
    
    params = analyze(func)
    
    assert 'theme' in params
    assert params['theme'].type == str
    assert params['theme'].default is None
    assert params['theme'].field_info is not None
    assert params['theme'].dynamic_func is None
    assert params['theme'].is_optional is False

def test_literal_int():
    def func(size: Literal[1, 2, 3]): 
        pass
    
    params = analyze(func)
    
    assert 'size' in params
    assert params['size'].type == int
    assert params['size'].default is None
    assert params['size'].field_info is not None
    assert params['size'].dynamic_func is None
    assert params['size'].is_optional is False

def test_literal_float():
    def func(multiplier: Literal[0.5, 1.0, 1.5, 2.0]):
        pass
    
    params = analyze(func)
    
    assert 'multiplier' in params
    assert params['multiplier'].type == float
    assert params['multiplier'].default is None
    assert params['multiplier'].field_info is not None
    assert params['multiplier'].dynamic_func is None
    assert params['multiplier'].is_optional is False

def test_literal_bool():
    def func(enabled: Literal[True, False]): 
        pass
    
    params = analyze(func)
    
    assert 'enabled' in params
    assert params['enabled'].type == bool
    assert params['enabled'].default is None
    assert params['enabled'].field_info is not None
    assert params['enabled'].dynamic_func is None
    assert params['enabled'].is_optional is False

def test_literal_with_default():
    def func(theme: Literal['light', 'dark'] = 'light'): 
        pass
    
    params = analyze(func)
    
    assert 'theme' in params
    assert params['theme'].type == str
    assert params['theme'].default == 'light'
    assert params['theme'].field_info is not None
    assert params['theme'].dynamic_func is None
    assert params['theme'].is_optional is False

def test_literal_single_option():
    def func(mode: Literal['readonly']): 
        pass
    
    params = analyze(func)
    
    assert 'mode' in params
    assert params['mode'].type == str
    assert params['mode'].default is None
    assert params['mode'].field_info is not None
    assert params['mode'].dynamic_func is None
    assert params['mode'].is_optional is False

def test_literal_invalid_default_raises():
    with pytest.raises(ValueError, match="not in options"):
        def func(theme: Literal['light', 'dark'] = 'neon'): 
            pass
        analyze(func)

def test_literal_mixed_types_raises():
    with pytest.raises(TypeError, match="mixed types"):
        def func(x: Literal[1, 'two', 3]): 
            pass
        analyze(func)

def test_literal_mixed_int_float_raises():
    with pytest.raises(TypeError, match="mixed types"):
        def func(x: Literal[1, 2.5, 3]):
            pass
        analyze(func)

def test_dynamic_literal_function():
    def get_options():
        return ['A', 'B', 'C']
    
    def func(choice: Literal[get_options]):
        pass
    
    params = analyze(func)
    
    assert 'choice' in params
    assert params['choice'].type == str
    assert params['choice'].default is None
    assert params['choice'].field_info is not None
    assert params['choice'].dynamic_func is get_options
    assert params['choice'].is_optional is False

def test_dynamic_literal_single_string():
    def get_option():
        return "Hello"
    
    def func(choice: Literal[get_option]):
        pass
    
    params = analyze(func)
    
    assert 'choice' in params
    assert params['choice'].type == str
    assert params['choice'].default is None
    assert params['choice'].field_info is not None
    assert params['choice'].dynamic_func is get_option
    assert params['choice'].is_optional is False

def test_dynamic_literal_returns_tuple():
    def get_options():
        return ('X', 'Y', 'Z')
    
    def func(choice: Literal[get_options]):
        pass
    
    params = analyze(func)
    
    assert 'choice' in params
    assert params['choice'].type == str
    assert params['choice'].default is None
    assert params['choice'].field_info is not None
    assert params['choice'].dynamic_func is get_options
    assert params['choice'].is_optional is False

def test_dynamic_literal_with_ints():
    def get_numbers():
        return [1, 2, 3, 4, 5]
    
    def func(number: Literal[get_numbers]):
        pass
    
    params = analyze(func)
    
    assert 'number' in params
    assert params['number'].type == int
    assert params['number'].default is None
    assert params['number'].field_info is not None
    assert params['number'].dynamic_func is get_numbers
    assert params['number'].is_optional is False

def test_dynamic_literal_with_floats():
    def get_values():
        return [0.1, 0.5, 1.0]
    
    def func(value: Literal[get_values]):
        pass
    
    params = analyze(func)
    
    assert 'value' in params
    assert params['value'].type == float
    assert params['value'].default is None
    assert params['value'].field_info is not None
    assert params['value'].dynamic_func is get_values
    assert params['value'].is_optional is False

def test_dynamic_literal_mixed_types_raises():
    def get_mixed():
        return [1, 'two', 3]
    
    with pytest.raises(TypeError, match="mixed types"):
        def func(x: Literal[get_mixed]): # type: ignore
            pass
        analyze(func)

def test_dynamic_literal_empty_raises():
    def get_empty():
        return []
    
    with pytest.raises(TypeError):
        def func(x: Literal[get_empty]): # type: ignore
            pass
        analyze(func)

# --- OPTIONAL TYPES ---

def test_optional_int():
    def func(x: int | None): 
        pass
    
    params = analyze(func)
    
    assert 'x' in params
    assert params['x'].type == int
    assert params['x'].default is None
    assert params['x'].field_info is None
    assert params['x'].dynamic_func is None
    assert params['x'].is_optional is True
    assert params['x'].optional_enabled is False

def test_optional_float():
    def func(price: float | None): 
        pass
    
    params = analyze(func)
    
    assert 'price' in params
    assert params['price'].type == float
    assert params['price'].default is None
    assert params['price'].field_info is None
    assert params['price'].dynamic_func is None
    assert params['price'].is_optional is True
    assert params['price'].optional_enabled is False

def test_optional_str():
    def func(name: str | None): 
        pass
    
    params = analyze(func)
    
    assert 'name' in params
    assert params['name'].type == str
    assert params['name'].default is None
    assert params['name'].field_info is None
    assert params['name'].dynamic_func is None
    assert params['name'].is_optional is True
    assert params['name'].optional_enabled is False

def test_optional_bool():
    def func(active: bool | None): 
        pass
    
    params = analyze(func)
    
    assert 'active' in params
    assert params['active'].type == bool
    assert params['active'].default is None
    assert params['active'].field_info is None
    assert params['active'].dynamic_func is None
    assert params['active'].is_optional is True
    assert params['active'].optional_enabled is False

def test_optional_date():
    def func(birthday: date | None): 
        pass
    
    params = analyze(func)
    
    assert 'birthday' in params
    assert params['birthday'].type == date
    assert params['birthday'].default is None
    assert params['birthday'].field_info is None
    assert params['birthday'].dynamic_func is None
    assert params['birthday'].is_optional is True
    assert params['birthday'].optional_enabled is False

def test_optional_time():
    def func(meeting: time | None): 
        pass
    
    params = analyze(func)
    
    assert 'meeting' in params
    assert params['meeting'].type == time
    assert params['meeting'].default is None
    assert params['meeting'].field_info is None
    assert params['meeting'].dynamic_func is None
    assert params['meeting'].is_optional is True
    assert params['meeting'].optional_enabled is False

def test_optional_int_with_default():
    def func(age: int | None = 25): 
        pass
    
    params = analyze(func)
    
    assert 'age' in params
    assert params['age'].type == int
    assert params['age'].default == 25
    assert params['age'].field_info is None
    assert params['age'].dynamic_func is None
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is True

def test_optional_str_with_default():
    def func(name: str | None = "John"): 
        pass
    
    params = analyze(func)
    
    assert 'name' in params
    assert params['name'].type == str
    assert params['name'].default == "John"
    assert params['name'].field_info is None
    assert params['name'].dynamic_func is None
    assert params['name'].is_optional is True
    assert params['name'].optional_enabled is True

def test_optional_without_default():
    def func(email: str | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'email' in params
    assert params['email'].type == str
    assert params['email'].default is None
    assert params['email'].field_info is None
    assert params['email'].dynamic_func is None
    assert params['email'].is_optional is True
    assert params['email'].optional_enabled is False

def test_optional_float_with_default():
    def func(price: float | None = 9.99): 
        pass
    
    params = analyze(func)
    
    assert 'price' in params
    assert params['price'].type == float
    assert params['price'].default == 9.99
    assert params['price'].field_info is None
    assert params['price'].dynamic_func is None
    assert params['price'].is_optional is True
    assert params['price'].optional_enabled is True

def test_optional_bool_with_default():
    def func(active: bool | None = True): 
        pass
    
    params = analyze(func)
    
    assert 'active' in params
    assert params['active'].type == bool
    assert params['active'].default is True
    assert params['active'].field_info is None
    assert params['active'].dynamic_func is None
    assert params['active'].is_optional is True
    assert params['active'].optional_enabled is True

def test_optional_date_with_default():
    default_date = date(2000, 1, 1)
    
    def func(birthday: date | None = default_date): 
        pass
    
    params = analyze(func)
    
    assert 'birthday' in params
    assert params['birthday'].type == date
    assert params['birthday'].default == default_date
    assert params['birthday'].field_info is None
    assert params['birthday'].dynamic_func is None
    assert params['birthday'].is_optional is True
    assert params['birthday'].optional_enabled is True

def test_optional_time_with_default():
    default_time = time(14, 30)
    
    def func(meeting: time | None = default_time): 
        pass
    
    params = analyze(func)
    
    assert 'meeting' in params
    assert params['meeting'].type == time
    assert params['meeting'].default == default_time
    assert params['meeting'].field_info is None
    assert params['meeting'].dynamic_func is None
    assert params['meeting'].is_optional is True
    assert params['meeting'].optional_enabled is True

def test_optional_with_constraints():
    def func(age: Annotated[int, Field(ge=18)] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'age' in params
    assert params['age'].type == int
    assert params['age'].default is None
    assert params['age'].field_info is not None
    assert params['age'].dynamic_func is None
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is False

def test_optional_with_constraints_and_default():
    def func(age: Annotated[int, Field(ge=18, le=100)] | None = 25): 
        pass
    
    params = analyze(func)
    
    assert 'age' in params
    assert params['age'].type == int
    assert params['age'].default == 25
    assert params['age'].field_info is not None
    assert params['age'].dynamic_func is None
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is True

def test_optional_str_with_length():
    def func(username: Annotated[str, Field(min_length=3)] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'username' in params
    assert params['username'].type == str
    assert params['username'].default is None
    assert params['username'].field_info is not None
    assert params['username'].dynamic_func is None
    assert params['username'].is_optional is True
    assert params['username'].optional_enabled is False

def test_optional_color():
    def func(color: Color | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'color' in params
    assert params['color'].type == str
    assert params['color'].default is None
    assert params['color'].field_info is not None
    assert params['color'].dynamic_func is None
    assert params['color'].is_optional is True
    assert params['color'].optional_enabled is False

def test_optional_email():
    def func(email: Email | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'email' in params
    assert params['email'].type == str
    assert params['email'].default is None
    assert params['email'].field_info is not None
    assert params['email'].dynamic_func is None
    assert params['email'].is_optional is True
    assert params['email'].optional_enabled is False

def test_optional_image_file():
    def func(photo: ImageFile | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'photo' in params
    assert params['photo'].type == str
    assert params['photo'].default is None
    assert params['photo'].field_info is not None
    assert params['photo'].dynamic_func is None
    assert params['photo'].is_optional is True
    assert params['photo'].optional_enabled is False

def test_optional_literal():
    def func(theme: Literal['light', 'dark'] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'theme' in params
    assert params['theme'].type == str
    assert params['theme'].default is None
    assert params['theme'].field_info is not None
    assert params['theme'].dynamic_func is None
    assert params['theme'].is_optional is True
    assert params['theme'].optional_enabled is False

def test_optional_literal_with_default():
    def func(theme: Literal['light', 'dark'] | None = 'light'): 
        pass
    
    params = analyze(func)
    
    assert 'theme' in params
    assert params['theme'].type == str
    assert params['theme'].default == 'light'
    assert params['theme'].field_info is not None
    assert params['theme'].dynamic_func is None
    assert params['theme'].is_optional is True
    assert params['theme'].optional_enabled is True

def test_optional_only_none_raises():
    with pytest.raises(TypeError):
        def func(x: Union[None, None]): 
            pass
        analyze(func)

def test_optional_multiple_types_raises():
    with pytest.raises(TypeError, match="multiple non-None types"):
        def func(x: int | str | None): 
            pass
        analyze(func)

# --- OPTIONAL ENABLED / DISABLED MARKERS ---

def test_optional_enabled_int():
    def func(x: int | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert 'x' in params
    assert params['x'].type == int
    assert params['x'].default is None
    assert params['x'].field_info is None
    assert params['x'].dynamic_func is None
    assert params['x'].is_optional is True
    assert params['x'].optional_enabled is True

def test_optional_enabled_str():
    def func(name: str | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert 'name' in params
    assert params['name'].type == str
    assert params['name'].default is None
    assert params['name'].is_optional is True
    assert params['name'].optional_enabled is True

def test_optional_enabled_float():
    def func(price: float | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert 'price' in params
    assert params['price'].type == float
    assert params['price'].is_optional is True
    assert params['price'].optional_enabled is True

def test_optional_enabled_bool():
    def func(active: bool | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert 'active' in params
    assert params['active'].type == bool
    assert params['active'].is_optional is True
    assert params['active'].optional_enabled is True

def test_optional_enabled_date():
    def func(birthday: date | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert 'birthday' in params
    assert params['birthday'].type == date
    assert params['birthday'].is_optional is True
    assert params['birthday'].optional_enabled is True

def test_optional_enabled_time():
    def func(meeting: time | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert 'meeting' in params
    assert params['meeting'].type == time
    assert params['meeting'].is_optional is True
    assert params['meeting'].optional_enabled is True

def test_optional_disabled_int():
    def func(x: int | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert 'x' in params
    assert params['x'].type == int
    assert params['x'].default is None
    assert params['x'].field_info is None
    assert params['x'].dynamic_func is None
    assert params['x'].is_optional is True
    assert params['x'].optional_enabled is False

def test_optional_disabled_str():
    def func(name: str | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert 'name' in params
    assert params['name'].type == str
    assert params['name'].default is None
    assert params['name'].is_optional is True
    assert params['name'].optional_enabled is False

def test_optional_disabled_float():
    def func(price: float | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert 'price' in params
    assert params['price'].type == float
    assert params['price'].is_optional is True
    assert params['price'].optional_enabled is False

def test_optional_disabled_bool():
    def func(active: bool | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert 'active' in params
    assert params['active'].type == bool
    assert params['active'].is_optional is True
    assert params['active'].optional_enabled is False

def test_optional_disabled_date():
    def func(birthday: date | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert 'birthday' in params
    assert params['birthday'].type == date
    assert params['birthday'].is_optional is True
    assert params['birthday'].optional_enabled is False

def test_optional_disabled_time():
    def func(meeting: time | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert 'meeting' in params
    assert params['meeting'].type == time
    assert params['meeting'].is_optional is True
    assert params['meeting'].optional_enabled is False

def test_optional_enabled_with_default_int():
    def func(age: int | OptionalEnabled = 25): 
        pass
    
    params = analyze(func)
    
    assert params['age'].type == int
    assert params['age'].default == 25
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is True

def test_optional_enabled_with_default_str():
    def func(name: str | OptionalEnabled = "John"): 
        pass
    
    params = analyze(func)
    
    assert params['name'].type == str
    assert params['name'].default == "John"
    assert params['name'].is_optional is True
    assert params['name'].optional_enabled is True

def test_optional_enabled_with_default_float():
    def func(price: float | OptionalEnabled = 9.99): 
        pass
    
    params = analyze(func)
    
    assert params['price'].type == float
    assert params['price'].default == 9.99
    assert params['price'].is_optional is True
    assert params['price'].optional_enabled is True

def test_optional_disabled_with_default_int():
    def func(age: int | OptionalDisabled = 25): 
        pass
    
    params = analyze(func)
    
    assert params['age'].type == int
    assert params['age'].default == 25
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is False

def test_optional_disabled_with_default_str():
    def func(name: str | OptionalDisabled = "John"): 
        pass
    
    params = analyze(func)
    
    assert params['name'].type == str
    assert params['name'].default == "John"
    assert params['name'].is_optional is True
    assert params['name'].optional_enabled is False

def test_optional_disabled_with_default_float():
    def func(price: float | OptionalDisabled = 9.99): 
        pass
    
    params = analyze(func)
    
    assert params['price'].type == float
    assert params['price'].default == 9.99
    assert params['price'].is_optional is True
    assert params['price'].optional_enabled is False

def test_optional_enabled_color():
    def func(color: Color | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert params['color'].type == str
    assert params['color'].field_info is not None
    assert params['color'].is_optional is True
    assert params['color'].optional_enabled is True

def test_optional_disabled_color():
    def func(color: Color | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert params['color'].type == str
    assert params['color'].field_info is not None
    assert params['color'].is_optional is True
    assert params['color'].optional_enabled is False

def test_optional_enabled_email():
    def func(email: Email | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert params['email'].type == str
    assert params['email'].field_info is not None
    assert params['email'].is_optional is True
    assert params['email'].optional_enabled is True

def test_optional_disabled_email():
    def func(email: Email | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert params['email'].type == str
    assert params['email'].field_info is not None
    assert params['email'].is_optional is True
    assert params['email'].optional_enabled is False

def test_optional_enabled_color_with_default():
    def func(color: Color | OptionalEnabled = "#ff0000"): 
        pass
    
    params = analyze(func)
    
    assert params['color'].type == str
    assert params['color'].default == "#ff0000"
    assert params['color'].field_info is not None
    assert params['color'].is_optional is True
    assert params['color'].optional_enabled is True

def test_optional_disabled_email_with_default():
    def func(email: Email | OptionalDisabled = "test@example.com"): 
        pass
    
    params = analyze(func)
    
    assert params['email'].type == str
    assert params['email'].default == "test@example.com"
    assert params['email'].field_info is not None
    assert params['email'].is_optional is True
    assert params['email'].optional_enabled is False

def test_optional_enabled_with_constraints():
    def func(age: Annotated[int, Field(ge=18, le=100)] | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert params['age'].type == int
    assert params['age'].field_info is not None
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is True

def test_optional_disabled_with_constraints():
    def func(age: Annotated[int, Field(ge=18, le=100)] | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert params['age'].type == int
    assert params['age'].field_info is not None
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is False

def test_optional_enabled_with_constraints_and_default():
    def func(age: Annotated[int, Field(ge=18, le=100)] | OptionalEnabled = 25): 
        pass
    
    params = analyze(func)
    
    assert params['age'].type == int
    assert params['age'].default == 25
    assert params['age'].field_info is not None
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is True

def test_optional_disabled_with_constraints_and_default():
    def func(age: Annotated[int, Field(ge=18, le=100)] | OptionalDisabled = 25): 
        pass
    
    params = analyze(func)
    
    assert params['age'].type == int
    assert params['age'].default == 25
    assert params['age'].field_info is not None
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is False

def test_auto_optional_without_default():
    def func(x: int | None): 
        pass
    
    params = analyze(func)
    
    assert params['x'].is_optional is True
    assert params['x'].optional_enabled is False

def test_auto_optional_with_default():
    def func(x: int | None = 42): 
        pass
    
    params = analyze(func)
    
    assert params['x'].is_optional is True
    assert params['x'].optional_enabled is True

def test_explicit_enabled_overrides_no_default():
    def func(x: int | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert params['x'].is_optional is True
    assert params['x'].optional_enabled is True

def test_explicit_disabled_overrides_default():
    def func(x: int | OptionalDisabled = 42): 
        pass
    
    params = analyze(func)
    
    assert params['x'].is_optional is True
    assert params['x'].optional_enabled is False

def test_optional_enabled_with_none_default():
    def func(x: int | OptionalEnabled = None): 
        pass
    
    params = analyze(func)
    
    assert params['x'].is_optional is True
    assert params['x'].default is None
    assert params['x'].optional_enabled is True

def test_optional_disabled_with_none_default():
    def func(x: int | OptionalDisabled = None): 
        pass
    
    params = analyze(func)
    
    assert params['x'].is_optional is True
    assert params['x'].default is None
    assert params['x'].optional_enabled is False

# --- LIST TYPES ---

def test_list_of_ints():
    def func(numbers: list[int]): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default is None
    assert params['numbers'].field_info is None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is False
    assert params['numbers'].is_list is True

def test_list_of_str():
    def func(names: list[str]): 
        pass
    
    params = analyze(func)
    
    assert 'names' in params
    assert params['names'].type == str
    assert params['names'].default is None
    assert params['names'].field_info is None
    assert params['names'].dynamic_func is None
    assert params['names'].is_optional is False
    assert params['names'].is_list is True

def test_list_of_floats():
    def func(prices: list[float]): 
        pass
    
    params = analyze(func)
    
    assert 'prices' in params
    assert params['prices'].type == float
    assert params['prices'].default is None
    assert params['prices'].field_info is None
    assert params['prices'].dynamic_func is None
    assert params['prices'].is_optional is False
    assert params['prices'].is_list is True

def test_list_of_bools():
    def func(flags: list[bool]): 
        pass
    
    params = analyze(func)
    
    assert 'flags' in params
    assert params['flags'].type == bool
    assert params['flags'].default is None
    assert params['flags'].field_info is None
    assert params['flags'].dynamic_func is None
    assert params['flags'].is_optional is False
    assert params['flags'].is_list is True

def test_list_of_dates():
    def func(dates: list[date]): 
        pass
    
    params = analyze(func)
    
    assert 'dates' in params
    assert params['dates'].type == date
    assert params['dates'].default is None
    assert params['dates'].field_info is None
    assert params['dates'].dynamic_func is None
    assert params['dates'].is_optional is False
    assert params['dates'].is_list is True

def test_list_of_times():
    def func(times: list[time]): 
        pass
    
    params = analyze(func)
    
    assert 'times' in params
    assert params['times'].type == time
    assert params['times'].default is None
    assert params['times'].field_info is None
    assert params['times'].dynamic_func is None
    assert params['times'].is_optional is False
    assert params['times'].is_list is True

def test_list_of_colors():
    def func(colors: list[Color]): 
        pass
    
    params = analyze(func)
    
    assert 'colors' in params
    assert params['colors'].type == str
    assert params['colors'].default is None
    assert params['colors'].field_info is not None
    assert params['colors'].dynamic_func is None
    assert params['colors'].is_optional is False
    assert params['colors'].is_list is True

def test_list_of_emails():
    def func(emails: list[Email]): 
        pass
    
    params = analyze(func)
    
    assert 'emails' in params
    assert params['emails'].type == str
    assert params['emails'].default is None
    assert params['emails'].field_info is not None
    assert params['emails'].dynamic_func is None
    assert params['emails'].is_optional is False
    assert params['emails'].is_list is True

def test_list_of_image_files():
    def func(photos: list[ImageFile]): 
        pass
    
    params = analyze(func)
    
    assert 'photos' in params
    assert params['photos'].type == str
    assert params['photos'].default is None
    assert params['photos'].field_info is not None
    assert params['photos'].dynamic_func is None
    assert params['photos'].is_optional is False
    assert params['photos'].is_list is True

def test_literal_default_raises():
    with pytest.raises(ValueError):
        def func(themes: Literal['light', 'dark'] = ["Aguacate"]):
            pass
        analyze(func)

def test_list_of_literal():
   with pytest.raises(TypeError, match="'themes': list of Literal not supported"):
        def func(themes: list[Literal['light', 'dark']]): 
            pass
        analyze(func)

def test_list_of_optional_raises():
    with pytest.raises(TypeError, match="'numbers': int | None not supported"):
        def func(numbers: list[int | None]): 
            pass
        analyze(func)

def test_list_of_list_raises():
    with pytest.raises(TypeError):
        def func(matrix: list[list[int]]): 
            pass
        analyze(func)

def test_list_of_list_raises():
    with pytest.raises(TypeError):
        def func(matrix: list[list]): 
            pass
        analyze(func)
    
# --- LIST WITH DEFAULT ---

def test_list_of_ints_with_default():
    def func(numbers: list[int] = [1, 2, 3]): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default == [1, 2, 3]
    assert params['numbers'].field_info is None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is False
    assert params['numbers'].is_list is True

def test_list_of_str_with_default():
    def func(names: list[str] = ["Alice", "Bob"]): 
        pass
    
    params = analyze(func)
    
    assert 'names' in params
    assert params['names'].type == str
    assert params['names'].default == ["Alice", "Bob"]
    assert params['names'].field_info is None
    assert params['names'].dynamic_func is None
    assert params['names'].is_optional is False
    assert params['names'].is_list is True

def test_list_of_floats_with_default():
    def func(prices: list[float] = [9.99, 19.99]): 
        pass
    
    params = analyze(func)
    
    assert 'prices' in params
    assert params['prices'].type == float
    assert params['prices'].default == [9.99, 19.99]
    assert params['prices'].field_info is None
    assert params['prices'].dynamic_func is None
    assert params['prices'].is_optional is False
    assert params['prices'].is_list is True

def test_list_of_bools_with_default():
    def func(flags: list[bool] = [True, False]): 
        pass
    
    params = analyze(func)
    
    assert 'flags' in params
    assert params['flags'].type == bool
    assert params['flags'].default == [True, False]
    assert params['flags'].field_info is None
    assert params['flags'].dynamic_func is None
    assert params['flags'].is_optional is False
    assert params['flags'].is_list is True

def test_list_of_dates_with_default():
    def func(dates: list[date] = [date(2023, 1, 1), date(2023, 12, 31)]): 
        pass
    
    params = analyze(func)
    
    assert 'dates' in params
    assert params['dates'].type == date
    assert params['dates'].default == [date(2023, 1, 1), date(2023, 12, 31)]
    assert params['dates'].field_info is None
    assert params['dates'].dynamic_func is None
    assert params['dates'].is_optional is False
    assert params['dates'].is_list is True

def test_list_of_times_with_default():
    def func(times: list[time] = [time(9, 0), time(17, 0)]): 
        pass
    
    params = analyze(func)
    
    assert 'times' in params
    assert params['times'].type == time
    assert params['times'].default == [time(9, 0), time(17, 0)]
    assert params['times'].field_info is None
    assert params['times'].dynamic_func is None
    assert params['times'].is_optional is False
    assert params['times'].is_list is True

def test_list_of_colors_with_default():
    def func(colors: list[Color] = ["#ff0000", "#00ff00"]): 
        pass
    
    params = analyze(func)
    
    assert 'colors' in params
    assert params['colors'].type == str
    assert params['colors'].default == ["#ff0000", "#00ff00"]
    assert params['colors'].field_info is not None
    assert params['colors'].dynamic_func is None
    assert params['colors'].is_optional is False
    assert params['colors'].is_list is True

def test_list_of_emails_with_default():
    def func(emails: list[Email] = ["aaa@gmail.com", "bbb@aaa.com"]):
        pass

    params = analyze(func)
    
    assert 'emails' in params
    assert params['emails'].type == str
    assert params['emails'].default == ["aaa@gmail.com", "bbb@aaa.com"]
    assert params['emails'].field_info is not None
    assert params['emails'].dynamic_func is None
    assert params['emails'].is_optional is False
    assert params['emails'].is_list is True
    
def test_list_of_image_files_with_default():
    def func(photos: list[ImageFile] = ["img1.png", "img2.jpg"]): 
        pass
    
    params = analyze(func)
    
    assert 'photos' in params
    assert params['photos'].type == str
    assert params['photos'].default == ["img1.png", "img2.jpg"]
    assert params['photos'].field_info is not None
    assert params['photos'].dynamic_func is None
    assert params['photos'].is_optional is False
    assert params['photos'].is_list is True

def test_default_list_empty():
    def func(numbers: list[int] = []): 
        pass
    params = analyze(func)
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default is None
    assert params['numbers'].field_info is None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is False
    assert params['numbers'].is_list is True

def test_list_of_literal_with_default():
    with pytest.raises(TypeError, match="'themes': list of Literal not supported"):
        def func(themes: list[Literal['light', 'dark']] = ['light']): 
            pass
        analyze(func)

def test_list_of_mixed_types_raises():
    with pytest.raises(TypeError):
        def func(items: list[Union[int, str]]): 
            pass
        analyze(func)

def test_list_of_mixed_types_with_default_raises():
    with pytest.raises(TypeError, match="'items': list item type mismatch in default"):
        def func(items: list[int] = [1, 'two']): 
            pass
        analyze(func)

def test_false_list():
    with pytest.raises(TypeError):
        def func(numbers: list[int] = "assf"): 
            pass
        analyze(func)

def test_false_list2():
    with pytest.raises(TypeError):
        def func(numbers: list[int] = (1,2)): 
            pass
        analyze(func)

def test_false_list3():
    with pytest.raises(TypeError):
        def func(numbers: list[int] = 3):
            pass
        analyze(func)

# --- LIST WITH CONSTRAINTS ---

def test_list_of_ints_with_constraints():
    def func(numbers: list[Annotated[int, Field(ge=0)]]): 
        pass
    params = analyze(func)
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default is None
    assert params['numbers'].field_info is not None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is False
    assert params['numbers'].is_list is True

def test_list_of_str_with_constraints():
    def func(names: list[Annotated[str, Field(min_length=2)]]): 
        pass
    params = analyze(func)
    assert 'names' in params
    assert params['names'].type == str
    assert params['names'].default is None
    assert params['names'].field_info is not None
    assert params['names'].dynamic_func is None
    assert params['names'].is_optional is False
    assert params['names'].is_list is True

def test_list_of_floats_with_constraints():
    def func(prices: list[Annotated[float, Field(gt=0.0)]]): 
        pass
    params = analyze(func)
    assert 'prices' in params
    assert params['prices'].type == float
    assert params['prices'].default is None
    assert params['prices'].field_info is not None
    assert params['prices'].dynamic_func is None
    assert params['prices'].is_optional is False
    assert params['prices'].is_list is True

def test_list_of_bools_with_constraints():
    def func(flags: list[Annotated[bool, Field()]]): 
        pass
    params = analyze(func)
    assert 'flags' in params
    assert params['flags'].type == bool
    assert params['flags'].default is None
    assert params['flags'].field_info is not None
    assert params['flags'].dynamic_func is None
    assert params['flags'].is_optional is False
    assert params['flags'].is_list is True

def test_list_of_dates_with_constraints():
    def func(dates: list[Annotated[date, Field()]]): 
        pass
    params = analyze(func)
    assert 'dates' in params
    assert params['dates'].type == date
    assert params['dates'].default is None
    assert params['dates'].field_info is not None
    assert params['dates'].dynamic_func is None
    assert params['dates'].is_optional is False
    assert params['dates'].is_list is True

def test_list_of_times_with_constraints():
    def func(times: list[Annotated[time, Field()]]): 
        pass
    params = analyze(func)
    assert 'times' in params
    assert params['times'].type == time
    assert params['times'].default is None
    assert params['times'].field_info is not None
    assert params['times'].dynamic_func is None
    assert params['times'].is_optional is False
    assert params['times'].is_list is True

# --- LIST WITH DEFAULT AND CONSTRAINTS ---

def test_list_of_ints_with_constraints_and_default():
    def func(numbers: list[Annotated[int, Field(ge=0)]] = [0, 1, 2]): 
        pass
    params = analyze(func)
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default == [0, 1, 2]
    assert params['numbers'].field_info is not None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is False
    assert params['numbers'].is_list is True

def test_list_of_str_with_constraints_and_default():
    def func(names: list[Annotated[str, Field(min_length=2)]] = ["Al", "Bo"]): 
        pass
    params = analyze(func)
    assert 'names' in params
    assert params['names'].type == str
    assert params['names'].default == ["Al", "Bo"]
    assert params['names'].field_info is not None
    assert params['names'].dynamic_func is None
    assert params['names'].is_optional is False
    assert params['names'].is_list is True

def test_list_of_floats_with_constraints_and_default():
    def func(prices: list[Annotated[float, Field(gt=0.0)]] = [9.99, 19.99]): 
        pass
    params = analyze(func)
    assert 'prices' in params
    assert params['prices'].type == float
    assert params['prices'].default == [9.99, 19.99]
    assert params['prices'].field_info is not None
    assert params['prices'].dynamic_func is None
    assert params['prices'].is_optional is False
    assert params['prices'].is_list is True

def test_list_of_bools_with_constraints_and_default():
    def func(flags: list[Annotated[bool, Field()]] = [True, False]): 
        pass
    params = analyze(func)
    assert 'flags' in params
    assert params['flags'].type == bool
    assert params['flags'].default == [True, False]
    assert params['flags'].field_info is not None
    assert params['flags'].dynamic_func is None
    assert params['flags'].is_optional is False
    assert params['flags'].is_list is True

def test_list_of_dates_with_constraints_and_default():
    def func(dates: list[Annotated[date, Field()]] = [date(2023, 1, 1), date(2023, 12, 31)]): 
        pass
    params = analyze(func)
    assert 'dates' in params
    assert params['dates'].type == date
    assert params['dates'].default == [date(2023, 1, 1), date(2023, 12, 31)]
    assert params['dates'].field_info is not None
    assert params['dates'].dynamic_func is None
    assert params['dates'].is_optional is False
    assert params['dates'].is_list is True

def test_error_default_constraint_mismatch():
    with pytest.raises(ValidationError):
        def func(numbers: list[Annotated[int, Field(ge=0)]] = [1, -2, 3]): 
            pass
        analyze(func)

def test_error_default_constraint_mismatch_str():
    with pytest.raises(ValidationError):
        def func(names: list[Annotated[str, Field(min_length=2)]] = ["A", "Bob"]): 
            pass
        analyze(func)

def test_error_default_constraint_mismatch_float():
    with pytest.raises(ValidationError):
        def func(prices: list[Annotated[float, Field(gt=0.0)]] = [9.99, -19.99]): 
            pass
        analyze(func)

def test_error_default_constraint_mismatch_email():
    with pytest.raises(ValidationError):
        def func(emails: list[Email] = ["aa"]): 
            pass
        analyze(func)

def test_error_default_constraint_mismatch_color():
    with pytest.raises(ValidationError):
        def func(colors: list[Color] = ["not-a-color"]): 
            pass
        analyze(func)

# --- LIST OPTIONAL ---

def test_optional_list_of_ints():
    def func(numbers: list[int] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default is None
    assert params['numbers'].field_info is None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is False
    assert params['numbers'].is_list is True

def test_optional_list_of_strs():
    def func(names: list[str] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'names' in params
    assert params['names'].type == str
    assert params['names'].default is None
    assert params['names'].field_info is None
    assert params['names'].dynamic_func is None
    assert params['names'].is_optional is True
    assert params['names'].optional_enabled is False
    assert params['names'].is_list is True

def test_optional_list_of_floats():
    def func(prices: list[float] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'prices' in params
    assert params['prices'].type == float
    assert params['prices'].default is None
    assert params['prices'].field_info is None
    assert params['prices'].dynamic_func is None
    assert params['prices'].is_optional is True
    assert params['prices'].optional_enabled is False
    assert params['prices'].is_list is True

def test_optional_list_of_bools():
    def func(flags: list[bool] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'flags' in params
    assert params['flags'].type == bool
    assert params['flags'].default is None
    assert params['flags'].field_info is None
    assert params['flags'].dynamic_func is None
    assert params['flags'].is_optional is True
    assert params['flags'].optional_enabled is False
    assert params['flags'].is_list is True

def test_optional_list_of_dates():
    def func(dates: list[date] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'dates' in params
    assert params['dates'].type == date
    assert params['dates'].default is None
    assert params['dates'].field_info is None
    assert params['dates'].dynamic_func is None
    assert params['dates'].is_optional is True
    assert params['dates'].optional_enabled is False
    assert params['dates'].is_list is True

def test_optional_list_of_times():
    def func(times: list[time] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'times' in params
    assert params['times'].type == time
    assert params['times'].default is None
    assert params['times'].field_info is None
    assert params['times'].dynamic_func is None
    assert params['times'].is_optional is True
    assert params['times'].optional_enabled is False
    assert params['times'].is_list is True

def test_optional_list_of_colors():
    def func(colors: list[Color] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'colors' in params
    assert params['colors'].type == str
    assert params['colors'].default is None
    assert params['colors'].field_info is not None
    assert params['colors'].dynamic_func is None
    assert params['colors'].is_optional is True
    assert params['colors'].optional_enabled is False
    assert params['colors'].is_list is True

def test_optional_list_of_emails():
    def func(emails: list[Email] | OptionalEnabled = None): 
        pass
    
    params = analyze(func)
    
    assert 'emails' in params
    assert params['emails'].type == str
    assert params['emails'].default is None
    assert params['emails'].field_info is not None
    assert params['emails'].dynamic_func is None
    assert params['emails'].is_optional is True
    assert params['emails'].optional_enabled is True
    assert params['emails'].is_list is True

# --- OPTIONAL LIST WITH NON-NONE DEFAULT ---

def test_optional_list_of_ints_with_default():
    def func(numbers: list[int] | None = [1, 2, 3]): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default == [1, 2, 3]
    assert params['numbers'].field_info is None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is True
    assert params['numbers'].is_list is True

def test_optional_list_of_strs_with_default():
    def func(names: list[str] | None = ["Alice", "Bob"]): 
        pass
    
    params = analyze(func)
    
    assert 'names' in params
    assert params['names'].type == str
    assert params['names'].default == ["Alice", "Bob"]
    assert params['names'].field_info is None
    assert params['names'].dynamic_func is None
    assert params['names'].is_optional is True
    assert params['names'].optional_enabled is True
    assert params['names'].is_list is True

def test_optional_list_of_floats_with_default():
    def func(prices: list[float] | None = [9.99, 19.99]): 
        pass
    
    params = analyze(func)
    
    assert 'prices' in params
    assert params['prices'].type == float
    assert params['prices'].default == [9.99, 19.99]
    assert params['prices'].field_info is None
    assert params['prices'].dynamic_func is None
    assert params['prices'].is_optional is True
    assert params['prices'].optional_enabled is True
    assert params['prices'].is_list is True

def test_optional_list_of_emails_disabled_with_default():
    def func(emails: list[Email] | OptionalDisabled = ["test@example.com"]): 
        pass
    
    params = analyze(func)
    
    assert 'emails' in params
    assert params['emails'].type == str
    assert params['emails'].default == ["test@example.com"]
    assert params['emails'].field_info is not None
    assert params['emails'].dynamic_func is None
    assert params['emails'].is_optional is True
    assert params['emails'].optional_enabled is False
    assert params['emails'].is_list is True

def test_optional_list_of_colors_enabled_with_default():
    def func(colors: list[Color] | OptionalEnabled = ["#ff0000", "#00ff00"]): 
        pass
    
    params = analyze(func)
    
    assert 'colors' in params
    assert params['colors'].type == str
    assert params['colors'].default == ["#ff0000", "#00ff00"]
    assert params['colors'].field_info is not None
    assert params['colors'].dynamic_func is None
    assert params['colors'].is_optional is True
    assert params['colors'].optional_enabled is True
    assert params['colors'].is_list is True

def test_optional_list_with_constraints():
    def func(numbers: list[Annotated[int, Field(ge=0)]] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default is None
    assert params['numbers'].field_info is not None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is False
    assert params['numbers'].is_list is True

def test_optional_list_with_constraints_and_default():
    def func(numbers: list[Annotated[int, Field(ge=0)]] | None = [1, 2, 3]): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default == [1, 2, 3]
    assert params['numbers'].field_info is not None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is True
    assert params['numbers'].is_list is True

def test_optional_list_with_constraints_enabled():
    def func(numbers: list[Annotated[int, Field(ge=0)]] | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default is None
    assert params['numbers'].field_info is not None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is True
    assert params['numbers'].is_list is True

def test_optional_list_with_constraints_disabled():
    def func(numbers: list[Annotated[int, Field(ge=0)]] | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default is None
    assert params['numbers'].field_info is not None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is False
    assert params['numbers'].is_list is True

def test_list_with_empty_default():
    def func(numbers: list[int] = []): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default == None
    assert params['numbers'].field_info is None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is False
    assert params['numbers'].is_list is True

def test_optional_list_with_empty_default():
    def func(numbers: list[int] | None = []): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default == None
    assert params['numbers'].field_info is None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is False
    assert params['numbers'].is_list is True


# --- LIST WITH LIST-LEVEL CONSTRAINTS ---

def test_list_with_list_level_constraints():
    def func(numbers: Annotated[list[int], Field(min_length=2, max_length=5)]):
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default is None
    assert params['numbers'].field_info is None
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is False
    assert params['numbers'].is_list is True

def test_list_with_min_items_only():
    def func(numbers: Annotated[list[int], Field(min_length=2)]):
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default is None
    assert params['numbers'].field_info is None
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_list is True

def test_list_with_max_items_only():
    def func(numbers: Annotated[list[int], Field(max_length=10)]):
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default is None
    assert params['numbers'].field_info is None
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_list is True

def test_list_with_both_item_and_list_constraints():
    def func(numbers: Annotated[list[Annotated[int, Field(ge=0, le=100)]], Field(min_length=2, max_length=5)]):
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default is None
    assert params['numbers'].field_info is not None  # Item constraints
    assert params['numbers'].list_field_info is not None  # List constraints
    assert params['numbers'].dynamic_func is None
    assert params['numbers'].is_optional is False
    assert params['numbers'].is_list is True

def test_list_with_list_constraints_and_default():
    def func(numbers: Annotated[list[int], Field(min_length=2, max_length=5)] = [1, 2, 3]): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default == [1, 2, 3]
    assert params['numbers'].field_info is None
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_list is True

def test_list_with_both_constraints_and_default():
    def func(numbers: Annotated[list[Annotated[int, Field(ge=0, le=100)]], Field(min_length=2, max_length=5)] = [10, 20, 30]): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default == [10, 20, 30]
    assert params['numbers'].field_info is not None
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_list is True

def test_list_str_with_list_constraints():
    def func(names: Annotated[list[str], Field(min_length=1, max_length=3)]): 
        pass
    
    params = analyze(func)
    
    assert 'names' in params
    assert params['names'].type == str
    assert params['names'].field_info is None
    assert params['names'].list_field_info is not None
    assert params['names'].is_list is True

def test_list_str_with_both_constraints():
    def func(names: Annotated[list[Annotated[str, Field(min_length=2, max_length=10)]], Field(min_length=1, max_length=3)]): 
        pass
    
    params = analyze(func)
    
    assert 'names' in params
    assert params['names'].type == str
    assert params['names'].field_info is not None
    assert params['names'].list_field_info is not None
    assert params['names'].is_list is True

def test_list_email_with_list_constraints():
    def func(emails: Annotated[list[Email], Field(min_length=1, max_length=5)]): 
        pass
    
    params = analyze(func)
    
    assert 'emails' in params
    assert params['emails'].type == str
    assert params['emails'].field_info is not None  # Email constraint
    assert params['emails'].list_field_info is not None  # List constraint
    assert params['emails'].is_list is True

def test_list_color_with_list_constraints():
    def func(colors: Annotated[list[Color], Field(min_length=2, max_length=10)]): 
        pass
    
    params = analyze(func)
    
    assert 'colors' in params
    assert params['colors'].type == str
    assert params['colors'].field_info is not None  # Color constraint
    assert params['colors'].list_field_info is not None  # List constraint
    assert params['colors'].is_list is True

# --- LIST VALIDATION WITH LIST-LEVEL CONSTRAINTS ---

def test_list_default_violates_min_items():
    with pytest.raises(ValidationError):
        def func(numbers: Annotated[list[int], Field(min_length=3)] = [1, 2]): 
            pass
        analyze(func)

def test_list_default_violates_max_items():
    with pytest.raises(ValidationError):
        def func(numbers: Annotated[list[int], Field(max_length=2)] = [1, 2, 3]): 
            pass
        analyze(func)

def test_list_default_satisfies_list_constraints():
    def func(numbers: Annotated[list[int], Field(min_length=2, max_length=5)] = [1, 2, 3]): 
        pass
    
    params = analyze(func)
    
    assert params['numbers'].default == [1, 2, 3]

def test_list_default_violates_both_item_and_list_constraints():
    with pytest.raises(ValidationError):
        def func(numbers: Annotated[list[Annotated[int, Field(ge=0)]], Field(min_length=2)] = [-1]): 
            pass
        analyze(func)

def test_list_default_violates_only_item_constraint():
    with pytest.raises(ValidationError):
        def func(numbers: Annotated[list[Annotated[int, Field(ge=0)]], Field(min_length=2)] = [-1, 1, 2]): 
            pass
        analyze(func)

def test_list_default_violates_only_list_constraint():
    with pytest.raises(ValidationError):
        def func(numbers: Annotated[list[Annotated[int, Field(ge=0)]], Field(min_length=2)] = [1]): 
            pass
        analyze(func)

def test_list_default_satisfies_both_constraints():
    def func(numbers: Annotated[list[Annotated[int, Field(ge=0, le=100)]], Field(min_length=2, max_length=5)] = [10, 20, 30]): 
        pass
    
    params = analyze(func)
    
    assert params['numbers'].default == [10, 20, 30]

def test_list_email_default_violates_list_constraint():
    with pytest.raises(ValidationError):
        def func(emails: Annotated[list[Email], Field(max_length=2)] = ["a@a.com", "b@b.com", "c@c.com"]): 
            pass
        analyze(func)

def test_list_color_default_violates_list_constraint():
    with pytest.raises(ValidationError):
        def func(colors: Annotated[list[Color], Field(min_length=2)] = ["#ff0000"]): 
            pass
        analyze(func)

# --- OPTIONAL LIST WITH LIST-LEVEL CONSTRAINTS ---

def test_optional_list_with_list_constraints():
    def func(numbers: Annotated[list[int], Field(min_length=2, max_length=5)] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].default is None
    assert params['numbers'].field_info is None
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is False
    assert params['numbers'].is_list is True

def test_optional_list_with_both_constraints():
    def func(numbers: Annotated[list[Annotated[int, Field(ge=0)]], Field(min_length=2)] | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].type == int
    assert params['numbers'].field_info is not None
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is False
    assert params['numbers'].is_list is True

def test_optional_list_with_list_constraints_and_default():
    def func(numbers: Annotated[list[int], Field(min_length=2, max_length=5)] | None = [1, 2, 3]): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].default == [1, 2, 3]
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is True
    assert params['numbers'].is_list is True

def test_optional_list_with_list_constraints_enabled():
    def func(numbers: Annotated[list[int], Field(min_length=2)] | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is True
    assert params['numbers'].is_list is True

def test_optional_list_with_list_constraints_disabled():
    def func(numbers: Annotated[list[int], Field(min_length=2)] | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is False
    assert params['numbers'].is_list is True

def test_optional_list_with_both_constraints_and_enabled():
    def func(numbers: Annotated[list[Annotated[int, Field(ge=0, le=100)]], Field(min_length=2, max_length=5)] | OptionalEnabled = [10, 20]): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].default == [10, 20]
    assert params['numbers'].field_info is not None
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is True
    assert params['numbers'].is_list is True

def test_list_empty_default_with_min_items_raises():
    with pytest.raises(ValidationError):
        def func(numbers: Annotated[list[int], Field(min_length=1)] = []): 
            pass
        analyze(func)

def test_list_with_min_items_zero():
    def func(numbers: Annotated[list[int], Field(min_length=0)] = []): 
        pass
    
    params = analyze(func)
    
    assert params['numbers'].default == None
    assert params['numbers'].list_field_info is not None

def test_list_with_min_length_only():
    def func(numbers: Annotated[list[int], Field(min_length=2)]): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_list is True

def test_list_with_max_length_only():
    def func(numbers: Annotated[list[int], Field(max_length=10)]): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_list is True

def test_optional_list_enabled_without_default():
    def func(numbers: list[int] | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].default is None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is True
    assert params['numbers'].is_list is True

def test_optional_list_disabled_without_default():
    def func(numbers: list[int] | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert 'numbers' in params
    assert params['numbers'].default is None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is False
    assert params['numbers'].is_list is True

def test_list_with_min_length_zero():
    def func(numbers: Annotated[list[int], Field(min_length=0)] = []): 
        pass
    
    params = analyze(func)
    
    assert params['numbers'].default is None
    assert params['numbers'].list_field_info is not None

def test_list_default_violates_max_length():
    with pytest.raises(ValidationError):
        def func(numbers: Annotated[list[int], Field(max_length=2)] = [1, 2, 3]): 
            pass
        analyze(func)

def test_list_default_violates_min_length():
    with pytest.raises(ValidationError):
        def func(numbers: Annotated[list[int], Field(min_length=3)] = [1, 2]): 
            pass
        analyze(func)

def test_optional_list_enabled_with_both_constraints():
    def func(numbers: Annotated[list[Annotated[int, Field(ge=0)]], Field(min_length=2, max_length=5)] | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert params['numbers'].field_info is not None
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is True
    assert params['numbers'].is_list is True

def test_optional_list_disabled_with_both_constraints():
    def func(numbers: Annotated[list[Annotated[int, Field(ge=0)]], Field(min_length=2, max_length=5)] | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert params['numbers'].field_info is not None
    assert params['numbers'].list_field_info is not None
    assert params['numbers'].is_optional is True
    assert params['numbers'].optional_enabled is False
    assert params['numbers'].is_list is True

def test_list_image_files_with_list_constraints():
    def func(photos: Annotated[list[ImageFile], Field(min_length=1, max_length=5)]): 
        pass
    
    params = analyze(func)
    
    assert params['photos'].type == str
    assert params['photos'].field_info is not None
    assert params['photos'].list_field_info is not None
    assert params['photos'].is_list is True

def test_list_data_files_with_list_constraints():
    def func(files: Annotated[list[DataFile], Field(min_length=1, max_length=3)]): 
        pass
    
    params = analyze(func)
    
    assert params['files'].type == str
    assert params['files'].field_info is not None
    assert params['files'].list_field_info is not None
    assert params['files'].is_list is True

def test_list_str_default_violates_item_min_length():
    with pytest.raises(ValidationError):
        def func(names: list[Annotated[str, Field(min_length=3)]] = ["AB", "CD"]): 
            pass
        analyze(func)

def test_list_str_default_violates_item_max_length():
    with pytest.raises(ValidationError):
        def func(names: list[Annotated[str, Field(max_length=5)]] = ["TOOLONG"]): 
            pass
        analyze(func)

def test_list_of_literal_ints_not_supported():
    with pytest.raises(TypeError):
        def func(numbers: list[Literal[1, 2, 3]]): 
            pass
        analyze(func)

# --- ENUM TYPES ---

def test_enum_string():
    from enum import Enum
    
    class Theme(Enum):
        LIGHT = 'light'
        DARK = 'dark'
        AUTO = 'auto'
    
    def func(theme: Theme): 
        pass
    
    params = analyze(func)
    
    assert 'theme' in params
    assert params['theme'].type == str
    assert params['theme'].default is None
    assert params['theme'].field_info is not None
    assert params['theme'].dynamic_func is None
    assert params['theme'].is_optional is False
    assert params['theme'].enum_type is Theme

def test_enum_int():
    from enum import Enum
    
    class Size(Enum):
        SMALL = 1
        MEDIUM = 2
        LARGE = 3
    
    def func(size: Size): 
        pass
    
    params = analyze(func)
    
    assert 'size' in params
    assert params['size'].type == int
    assert params['size'].default is None
    assert params['size'].field_info is not None
    assert params['size'].dynamic_func is None
    assert params['size'].is_optional is False
    assert params['size'].enum_type is Size

def test_enum_float():
    from enum import Enum
    
    class Multiplier(Enum):
        HALF = 0.5
        NORMAL = 1.0
        DOUBLE = 2.0
    
    def func(multiplier: Multiplier):
        pass
    
    params = analyze(func)
    
    assert 'multiplier' in params
    assert params['multiplier'].type == float
    assert params['multiplier'].default is None
    assert params['multiplier'].field_info is not None
    assert params['multiplier'].dynamic_func is None
    assert params['multiplier'].is_optional is False
    assert params['multiplier'].enum_type is Multiplier

def test_enum_with_default():
    from enum import Enum
    
    class Theme(Enum):
        LIGHT = 'light'
        DARK = 'dark'
    
    def func(theme: Theme = Theme.LIGHT): 
        pass
    
    params = analyze(func)
    
    assert 'theme' in params
    assert params['theme'].type == str
    assert params['theme'].default == 'light'  # Converted to value
    assert params['theme'].field_info is not None
    assert params['theme'].dynamic_func is None
    assert params['theme'].is_optional is False
    assert params['theme'].enum_type is Theme

def test_enum_single_option():
    from enum import Enum
    
    class Mode(Enum):
        READONLY = 'readonly'
    
    def func(mode: Mode): 
        pass
    
    params = analyze(func)
    
    assert 'mode' in params
    assert params['mode'].type == str
    assert params['mode'].default is None
    assert params['mode'].field_info is not None
    assert params['mode'].dynamic_func is None
    assert params['mode'].is_optional is False
    assert params['mode'].enum_type is Mode

def test_enum_invalid_default_raises():
    from enum import Enum
    
    class Theme(Enum):
        LIGHT = 'light'
        DARK = 'dark'
    
    with pytest.raises(TypeError, match="default must be Theme instance"):
        def func(theme: Theme = 'neon'): 
            pass
        analyze(func)

def test_enum_mixed_types_raises():
    from enum import Enum
    
    class Mixed(Enum):
        ONE = 1
        TWO = 'two'
        THREE = 3
    
    with pytest.raises(TypeError, match="Enum values must be same type"):
        def func(x: Mixed): 
            pass
        analyze(func)

def test_enum_mixed_int_float_raises():
    from enum import Enum
    
    class Mixed(Enum):
        INT = 1
        FLOAT = 2.5
        ANOTHER = 3
    
    with pytest.raises(TypeError, match="Enum values must be same type"):
        def func(x: Mixed):
            pass
        analyze(func)

def test_enum_empty_raises():
    from enum import Enum
    
    class Empty(Enum):
        pass
    
    with pytest.raises(ValueError, match="Enum must have at least one value"):
        def func(x: Empty): 
            pass
        analyze(func)

# --- OPTIONAL ENUM TYPES ---

def test_optional_enum():
    from enum import Enum
    
    class Theme(Enum):
        LIGHT = 'light'
        DARK = 'dark'
    
    def func(theme: Theme | None = None): 
        pass
    
    params = analyze(func)
    
    assert 'theme' in params
    assert params['theme'].type == str
    assert params['theme'].default is None
    assert params['theme'].field_info is not None
    assert params['theme'].dynamic_func is None
    assert params['theme'].is_optional is True
    assert params['theme'].optional_enabled is False
    assert params['theme'].enum_type is Theme

def test_optional_enum_with_default():
    from enum import Enum
    
    class Theme(Enum):
        LIGHT = 'light'
        DARK = 'dark'
    
    def func(theme: Theme | None = Theme.LIGHT): 
        pass
    
    params = analyze(func)
    
    assert 'theme' in params
    assert params['theme'].type == str
    assert params['theme'].default == 'light'
    assert params['theme'].field_info is not None
    assert params['theme'].dynamic_func is None
    assert params['theme'].is_optional is True
    assert params['theme'].optional_enabled is True
    assert params['theme'].enum_type is Theme

def test_optional_enum_enabled():
    from enum import Enum
    
    class Color(Enum):
        RED = 'red'
        BLUE = 'blue'
    
    def func(color: Color | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert 'color' in params
    assert params['color'].type == str
    assert params['color'].default is None
    assert params['color'].is_optional is True
    assert params['color'].optional_enabled is True
    assert params['color'].enum_type is Color

def test_optional_enum_disabled():
    from enum import Enum
    
    class Color(Enum):
        RED = 'red'
        BLUE = 'blue'
    
    def func(color: Color | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert 'color' in params
    assert params['color'].type == str
    assert params['color'].default is None
    assert params['color'].is_optional is True
    assert params['color'].optional_enabled is False
    assert params['color'].enum_type is Color

def test_optional_enum_enabled_with_default():
    from enum import Enum
    
    class Theme(Enum):
        LIGHT = 'light'
        DARK = 'dark'
    
    def func(theme: Theme | OptionalEnabled = Theme.DARK): 
        pass
    
    params = analyze(func)
    
    assert params['theme'].type == str
    assert params['theme'].default == 'dark'
    assert params['theme'].is_optional is True
    assert params['theme'].optional_enabled is True
    assert params['theme'].enum_type is Theme

def test_optional_enum_disabled_with_default():
    from enum import Enum
    
    class Theme(Enum):
        LIGHT = 'light'
        DARK = 'dark'
    
    def func(theme: Theme | OptionalDisabled = Theme.DARK): 
        pass
    
    params = analyze(func)
    
    assert params['theme'].type == str
    assert params['theme'].default == 'dark'
    assert params['theme'].is_optional is True
    assert params['theme'].optional_enabled is False
    assert params['theme'].enum_type is Theme

def test_enum_int_with_default():
    from enum import Enum
    
    class Priority(Enum):
        LOW = 1
        MEDIUM = 2
        HIGH = 3
    
    def func(priority: Priority = Priority.MEDIUM): 
        pass
    
    params = analyze(func)
    
    assert params['priority'].type == int
    assert params['priority'].default == 2
    assert params['priority'].enum_type is Priority

def test_enum_float_with_default():
    from enum import Enum
    
    class Speed(Enum):
        SLOW = 0.5
        NORMAL = 1.0
        FAST = 2.0
    
    def func(speed: Speed = Speed.NORMAL): 
        pass
    
    params = analyze(func)
    
    assert params['speed'].type == float
    assert params['speed'].default == 1.0
    assert params['speed'].enum_type is Speed

def test_explicit_enabled_overrides_no_default_enum():
    from enum import Enum
    
    class Theme(Enum):
        LIGHT = 'light'
        DARK = 'dark'
    
    def func(theme: Theme | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert params['theme'].is_optional is True
    assert params['theme'].optional_enabled is True
    assert params['theme'].enum_type is Theme

def test_explicit_disabled_overrides_default_enum():
    from enum import Enum
    
    class Theme(Enum):
        LIGHT = 'light'
        DARK = 'dark'
    
    def func(theme: Theme | OptionalDisabled = Theme.LIGHT): 
        pass
    
    params = analyze(func)
    
    assert params['theme'].is_optional is True
    assert params['theme'].default == 'light'
    assert params['theme'].optional_enabled is False
    assert params['theme'].enum_type is Theme

def test_optional_enum_with_none_default():
    from enum import Enum
    
    class Theme(Enum):
        LIGHT = 'light'
        DARK = 'dark'
    
    def func(theme: Theme | OptionalEnabled = None): 
        pass
    
    params = analyze(func)
    
    assert params['theme'].is_optional is True
    assert params['theme'].default is None
    assert params['theme'].optional_enabled is True
    assert params['theme'].enum_type is Theme

# --- ENUM WITH STRING VALUES (STRENUM) ---

def test_string_enum():
    from enum import Enum
    
    class Status(Enum):
        PENDING = "pending"
        APPROVED = "approved"
        REJECTED = "rejected"
    
    def func(status: Status):
        pass
    
    params = analyze(func)
    
    assert params['status'].type == str
    assert params['status'].enum_type is Status
    assert params['status'].field_info is not None