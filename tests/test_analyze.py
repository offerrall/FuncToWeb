import pytest
from datetime import date, time
from func_to_web import *
from func_to_web.types import *

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
    with pytest.raises(TypeError, match="not supported"):
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


def test_optional_only_none_raises():
    from typing import Union
    
    with pytest.raises(TypeError):
        def func(x: Union[None, None]): 
            pass
        analyze(func)

def test_optional_multiple_types_raises():
    with pytest.raises(TypeError, match="multiple non-None types"):
        def func(x: int | str | None): 
            pass
        analyze(func)


def test_complex_function_all_features():
    def get_modes():
        return ['fast', 'slow']
    
    def func(
        name: str,
        age: int,
        active: bool,
        username: Annotated[str, Field(min_length=3, max_length=20)],
        color: Color,
        score: float = 9.5,
        rating: Annotated[int, Field(ge=1, le=10)] = 5,
        theme: Literal['light', 'dark'] = 'light',
        email: Email | None = None,
        mode: Literal[get_modes] | None = None, 
        bio: str | None = None,
        birthday: date | None = None,
        password: Annotated[str, Field(min_length=8)] | None = None,
    ): 
        pass
    
    params = analyze(func)
    
    assert len(params) == 13
    
    assert params['name'].type == str
    assert params['name'].is_optional is False
    assert params['age'].type == int
    assert params['age'].is_optional is False
    assert params['active'].type == bool
    assert params['active'].is_optional is False
    
    assert params['score'].type == float
    assert params['score'].default == 9.5
    assert params['score'].is_optional is False
    
    assert params['username'].type == str
    assert params['username'].field_info is not None
    assert params['username'].is_optional is False
    assert params['rating'].type == int
    assert params['rating'].default == 5
    assert params['rating'].field_info is not None
    
    assert params['color'].type == str
    assert params['color'].field_info is not None
    assert params['color'].is_optional is False
    assert params['email'].type == str
    assert params['email'].is_optional is True
    
    assert params['theme'].type == str
    assert params['theme'].default == 'light'
    assert params['theme'].field_info is not None
    assert params['theme'].dynamic_func is None
    
    assert params['mode'].type == str
    assert params['mode'].dynamic_func is get_modes
    
    assert params['bio'].type == str
    assert params['bio'].is_optional is True
    assert params['birthday'].type == date
    assert params['birthday'].is_optional is True
    
    assert params['password'].type == str
    assert params['password'].field_info is not None
    assert params['password'].is_optional is True


def test_multiple_optionals_with_mixed_defaults():
    def func(
        opt1: int | None,
        opt2: int | None = None,
        opt3: int | None = 42,
        opt4: str | None = "hello",
    ): 
        pass
    
    params = analyze(func)
    
    assert len(params) == 4
    
    assert params['opt1'].is_optional is True
    assert params['opt1'].default is None
    
    assert params['opt2'].is_optional is True
    assert params['opt2'].default is None
    
    assert params['opt3'].is_optional is True
    assert params['opt3'].default == 42
    
    assert params['opt4'].is_optional is True
    assert params['opt4'].default == "hello"


def test_all_basic_types_together():
    def func(
        a: int,
        b: float,
        c: str,
        d: bool,
        e: date,
        f: time,
    ): 
        pass
    
    params = analyze(func)
    
    assert len(params) == 6
    assert params['a'].type == int
    assert params['b'].type == float
    assert params['c'].type == str
    assert params['d'].type == bool
    assert params['e'].type == date
    assert params['f'].type == time


def test_all_special_types_together():
    def func(
        color: Color,
        email: Email,
        img: ImageFile,
        data: DataFile,
        txt: TextFile,
        doc: DocumentFile,
    ): 
        pass
    
    params = analyze(func)
    
    assert len(params) == 6
    
    for name in params:
        assert params[name].type == str
        assert params[name].field_info is not None


def test_multiple_literals_different_types():
    def func(
        str_lit: Literal['a', 'b', 'c'],
        int_lit: Literal[1, 2, 3],
        float_lit: Literal[0.1, 0.5, 1.0], # type: ignore
        bool_lit: Literal[True, False],
    ): 
        pass
    
    params = analyze(func)
    
    assert len(params) == 4
    assert params['str_lit'].type == str
    assert params['int_lit'].type == int
    assert params['float_lit'].type == float
    assert params['bool_lit'].type == bool


def test_nested_annotated_optional_no_default():
    def func(
        field1: Annotated[int, Field(ge=0)] | None,
        field2: Annotated[str, Field(min_length=5)] | None = "hello",
    ): 
        pass
    
    params = analyze(func)
    
    assert params['field1'].type == int
    assert params['field1'].field_info is not None
    assert params['field1'].is_optional is True
    assert params['field1'].default is None
    
    assert params['field2'].type == str
    assert params['field2'].field_info is not None
    assert params['field2'].is_optional is True
    assert params['field2'].default == "hello"


def test_all_constraints_in_one():
    def func(
        age: Annotated[int, Field(ge=18, le=100)],
        username: Annotated[str, Field(min_length=3, max_length=20)],
        rating: Annotated[float, Field(gt=0, lt=5)],
    ): 
        pass
    
    params = analyze(func)
    
    assert len(params) == 3
    assert params['age'].field_info is not None
    assert params['username'].field_info is not None
    assert params['rating'].field_info is not None

import pytest
from datetime import date, time
from func_to_web import analyze
from func_to_web.types import OptionalEnabled, OptionalDisabled, Color, Email


# Basic OptionalEnabled tests
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


# Basic OptionalDisabled tests
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


# Tests with defaults - OptionalEnabled
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


# Tests with defaults - OptionalDisabled (marker overrides default)
def test_optional_disabled_with_default_int():
    def func(age: int | OptionalDisabled = 25): 
        pass
    
    params = analyze(func)
    
    assert params['age'].type == int
    assert params['age'].default == 25
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is False  # Marker overrides default


def test_optional_disabled_with_default_str():
    def func(name: str | OptionalDisabled = "John"): 
        pass
    
    params = analyze(func)
    
    assert params['name'].type == str
    assert params['name'].default == "John"
    assert params['name'].is_optional is True
    assert params['name'].optional_enabled is False  # Marker overrides default


def test_optional_disabled_with_default_float():
    def func(price: float | OptionalDisabled = 9.99): 
        pass
    
    params = analyze(func)
    
    assert params['price'].type == float
    assert params['price'].default == 9.99
    assert params['price'].is_optional is True
    assert params['price'].optional_enabled is False  # Marker overrides default


# Tests with special types
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


# Tests with constraints
def test_optional_enabled_with_constraints():
    from pydantic import Field
    from typing import Annotated
    
    def func(age: Annotated[int, Field(ge=18, le=100)] | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert params['age'].type == int
    assert params['age'].field_info is not None
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is True


def test_optional_disabled_with_constraints():
    from pydantic import Field
    from typing import Annotated
    
    def func(age: Annotated[int, Field(ge=18, le=100)] | OptionalDisabled): 
        pass
    
    params = analyze(func)
    
    assert params['age'].type == int
    assert params['age'].field_info is not None
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is False


def test_optional_enabled_with_constraints_and_default():
    from pydantic import Field
    from typing import Annotated
    
    def func(age: Annotated[int, Field(ge=18, le=100)] | OptionalEnabled = 25): 
        pass
    
    params = analyze(func)
    
    assert params['age'].type == int
    assert params['age'].default == 25
    assert params['age'].field_info is not None
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is True


def test_optional_disabled_with_constraints_and_default():
    from pydantic import Field
    from typing import Annotated
    
    def func(age: Annotated[int, Field(ge=18, le=100)] | OptionalDisabled = 25): 
        pass
    
    params = analyze(func)
    
    assert params['age'].type == int
    assert params['age'].default == 25
    assert params['age'].field_info is not None
    assert params['age'].is_optional is True
    assert params['age'].optional_enabled is False  # Marker overrides default


# Comparison tests: automatic vs explicit behavior
def test_auto_optional_without_default():
    """Standard: int | None without default → disabled"""
    def func(x: int | None): 
        pass
    
    params = analyze(func)
    
    assert params['x'].is_optional is True
    assert params['x'].optional_enabled is False  # Auto: disabled (no default)


def test_auto_optional_with_default():
    """Standard: int | None with default → enabled"""
    def func(x: int | None = 42): 
        pass
    
    params = analyze(func)
    
    assert params['x'].is_optional is True
    assert params['x'].optional_enabled is True  # Auto: enabled (has default)


def test_explicit_enabled_overrides_no_default():
    """Explicit: OptionalEnabled without default → enabled"""
    def func(x: int | OptionalEnabled): 
        pass
    
    params = analyze(func)
    
    assert params['x'].is_optional is True
    assert params['x'].optional_enabled is True  # Explicit overrides


def test_explicit_disabled_overrides_default():
    """Explicit: OptionalDisabled with default → disabled"""
    def func(x: int | OptionalDisabled = 42): 
        pass
    
    params = analyze(func)
    
    assert params['x'].is_optional is True
    assert params['x'].optional_enabled is False  # Explicit overrides


# Mixed usage in one function
def test_mixed_optional_styles():
    """Test all three styles together"""
    def func(
        auto_disabled: int | None,  # Auto: no default → disabled
        explicit_enabled: int | OptionalEnabled,  # Explicit → enabled
        auto_enabled: int | None = 10,  # Auto: has default → enabled
        explicit_disabled: int | OptionalDisabled = 20,  # Explicit → disabled (overrides default)
    ): 
        pass
    
    params = analyze(func)
    
    assert params['auto_disabled'].optional_enabled is False
    assert params['auto_enabled'].optional_enabled is True
    assert params['explicit_enabled'].optional_enabled is True
    assert params['explicit_disabled'].optional_enabled is False


# Edge cases
def test_optional_enabled_with_none_default():
    """OptionalEnabled with explicit None default → still enabled"""
    def func(x: int | OptionalEnabled = None): 
        pass
    
    params = analyze(func)
    
    assert params['x'].is_optional is True
    assert params['x'].default is None
    assert params['x'].optional_enabled is True  # Marker takes priority


def test_optional_disabled_with_none_default():
    """OptionalDisabled with explicit None default → disabled"""
    def func(x: int | OptionalDisabled = None): 
        pass
    
    params = analyze(func)
    
    assert params['x'].is_optional is True
    assert params['x'].default is None
    assert params['x'].optional_enabled is False