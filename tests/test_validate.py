import pytest
from datetime import date, time
from func_to_web import *
from func_to_web.validate_params import validate_params


def test_int_parameter():
    def func(x: int): 
        pass
    
    params = analyze(func)
    form_data = {'x': '42'}
    
    validated = validate_params(form_data, params)
    
    assert validated['x'] == 42
    assert isinstance(validated['x'], int)


def test_float_parameter():
    def func(price: float): 
        pass
    
    params = analyze(func)
    form_data = {'price': '9.99'}
    
    validated = validate_params(form_data, params)
    
    assert validated['price'] == 9.99
    assert isinstance(validated['price'], float)


def test_str_parameter():
    def func(name: str): 
        pass
    
    params = analyze(func)
    form_data = {'name': 'John'}
    
    validated = validate_params(form_data, params)
    
    assert validated['name'] == 'John'
    assert isinstance(validated['name'], str)


def test_bool_parameter_checked():
    def func(active: bool): 
        pass
    
    params = analyze(func)
    form_data = {'active': 'on'}
    
    validated = validate_params(form_data, params)
    
    assert validated['active'] is True


def test_bool_parameter_unchecked():
    def func(active: bool): 
        pass
    
    params = analyze(func)
    form_data = {}
    
    validated = validate_params(form_data, params)
    
    assert validated['active'] is False


def test_date_parameter():
    def func(birthday: date): 
        pass
    
    params = analyze(func)
    form_data = {'birthday': '2000-01-01'}
    
    validated = validate_params(form_data, params)
    
    assert validated['birthday'] == date(2000, 1, 1)
    assert isinstance(validated['birthday'], date)


def test_time_parameter():
    def func(meeting: time): 
        pass
    
    params = analyze(func)
    form_data = {'meeting': '14:30'}
    
    validated = validate_params(form_data, params)
    
    assert validated['meeting'] == time(14, 30)
    assert isinstance(validated['meeting'], time)


def test_date_empty_value():
    def func(birthday: date): 
        pass
    
    params = analyze(func)
    form_data = {'birthday': ''}
    
    validated = validate_params(form_data, params)
    
    assert validated['birthday'] is None


def test_time_empty_value():
    def func(meeting: time): 
        pass
    
    params = analyze(func)
    form_data = {'meeting': ''}
    
    validated = validate_params(form_data, params)
    
    assert validated['meeting'] is None


def test_int_with_constraints_valid():
    def func(age: Annotated[int, Field(ge=0, le=120)]): 
        pass
    
    params = analyze(func)
    form_data = {'age': '25'}
    
    validated = validate_params(form_data, params)
    
    assert validated['age'] == 25


def test_int_below_minimum_raises():
    def func(age: Annotated[int, Field(ge=18)]): 
        pass
    
    params = analyze(func)
    form_data = {'age': '10'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_int_above_maximum_raises():
    def func(age: Annotated[int, Field(le=100)]): 
        pass
    
    params = analyze(func)
    form_data = {'age': '150'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_float_below_gt_raises():
    def func(rating: Annotated[float, Field(gt=0)]): 
        pass
    
    params = analyze(func)
    form_data = {'rating': '0.0'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_float_above_lt_raises():
    def func(rating: Annotated[float, Field(lt=5)]): 
        pass
    
    params = analyze(func)
    form_data = {'rating': '5.0'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_str_too_short_raises():
    def func(username: Annotated[str, Field(min_length=3)]): 
        pass
    
    params = analyze(func)
    form_data = {'username': 'ab'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_str_too_long_raises():
    def func(bio: Annotated[str, Field(max_length=10)]): 
        pass
    
    params = analyze(func)
    form_data = {'bio': 'a' * 20}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_str_within_length_valid():
    def func(username: Annotated[str, Field(min_length=3, max_length=20)]): 
        pass
    
    params = analyze(func)
    form_data = {'username': 'john'}
    
    validated = validate_params(form_data, params)
    
    assert validated['username'] == 'john'


def test_color_valid_hex6():
    def func(color: Color): 
        pass
    
    params = analyze(func)
    form_data = {'color': '#ff0000'}
    
    validated = validate_params(form_data, params)
    
    assert validated['color'] == '#ff0000'


def test_color_valid_hex3_expands():
    def func(color: Color): 
        pass
    
    params = analyze(func)
    form_data = {'color': '#f00'}
    
    validated = validate_params(form_data, params)
    
    assert validated['color'] == '#ff0000'


def test_color_invalid_raises():
    def func(color: Color): 
        pass
    
    params = analyze(func)
    form_data = {'color': 'red'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_email_valid():
    def func(email: Email): 
        pass
    
    params = analyze(func)
    form_data = {'email': 'test@example.com'}
    
    validated = validate_params(form_data, params)
    
    assert validated['email'] == 'test@example.com'


def test_email_invalid_raises():
    def func(email: Email): 
        pass
    
    params = analyze(func)
    form_data = {'email': 'notanemail'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_literal_string_valid():
    def func(theme: Literal['light', 'dark']): 
        pass
    
    params = analyze(func)
    form_data = {'theme': 'light'}
    
    validated = validate_params(form_data, params)
    
    assert validated['theme'] == 'light'


def test_literal_string_invalid_raises():
    def func(theme: Literal['light', 'dark']): 
        pass
    
    params = analyze(func)
    form_data = {'theme': 'neon'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_literal_int_valid():
    def func(size: Literal[1, 2, 3]): 
        pass
    
    params = analyze(func)
    form_data = {'size': '2'}
    
    validated = validate_params(form_data, params)
    
    assert validated['size'] == 2
    assert isinstance(validated['size'], int)


def test_literal_int_invalid_raises():
    def func(size: Literal[1, 2, 3]): 
        pass
    
    params = analyze(func)
    form_data = {'size': '5'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_literal_float_valid():
    def func(multiplier: Literal[0.5, 1.0, 1.5]): 
        pass
    
    params = analyze(func)
    form_data = {'multiplier': '1.0'}
    
    validated = validate_params(form_data, params)
    
    assert validated['multiplier'] == 1.0
    assert isinstance(validated['multiplier'], float)


def test_dynamic_literal_skips_validation():
    def get_options():
        return ['A', 'B', 'C']
    
    def func(choice: Literal[get_options]): 
        pass
    
    params = analyze(func)
    # Simulate that options changed after form render
    form_data = {'choice': 'D'}
    
    # Should NOT raise because dynamic literals skip validation
    validated = validate_params(form_data, params)
    
    assert validated['choice'] == 'D'


def test_optional_disabled():
    def func(name: str | None): 
        pass
    
    params = analyze(func)
    form_data = {'name': 'John'}
    # No toggle in form_data means disabled
    
    validated = validate_params(form_data, params)
    
    assert validated['name'] is None


def test_optional_enabled_with_value():
    def func(name: str | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'name': 'John',
        'name_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['name'] == 'John'


def test_optional_enabled_empty_value():
    def func(name: str | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'name': '',
        'name_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['name'] is None


def test_optional_int_enabled():
    def func(age: int | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'age': '25',
        'age_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['age'] == 25


def test_optional_int_disabled():
    def func(age: int | None): 
        pass
    
    params = analyze(func)
    form_data = {'age': '25'}
    
    validated = validate_params(form_data, params)
    
    assert validated['age'] is None


def test_optional_with_constraints_enabled_valid():
    def func(age: Annotated[int, Field(ge=18)] | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'age': '25',
        'age_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['age'] == 25


def test_optional_with_constraints_enabled_invalid_raises():
    def func(age: Annotated[int, Field(ge=18)] | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'age': '10',
        'age_optional_toggle': 'on'
    }
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_optional_date_enabled():
    def func(birthday: date | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'birthday': '2000-01-01',
        'birthday_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['birthday'] == date(2000, 1, 1)


def test_optional_date_disabled():
    def func(birthday: date | None): 
        pass
    
    params = analyze(func)
    form_data = {'birthday': '2000-01-01'}
    
    validated = validate_params(form_data, params)
    
    assert validated['birthday'] is None


def test_optional_time_enabled():
    def func(meeting: time | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'meeting': '14:30',
        'meeting_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['meeting'] == time(14, 30)


def test_optional_time_disabled():
    def func(meeting: time | None): 
        pass
    
    params = analyze(func)
    form_data = {'meeting': '14:30'}
    
    validated = validate_params(form_data, params)
    
    assert validated['meeting'] is None


def test_optional_bool_enabled_checked():
    def func(active: bool | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'active': 'on',
        'active_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['active'] is True


def test_optional_bool_enabled_unchecked():
    def func(active: bool | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'active_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['active'] is False


def test_optional_bool_disabled():
    def func(active: bool | None): 
        pass
    
    params = analyze(func)
    form_data = {'active': 'on'}
    
    validated = validate_params(form_data, params)
    
    assert validated['active'] is None


def test_optional_literal_enabled():
    def func(theme: Literal['light', 'dark'] | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'theme': 'dark',
        'theme_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['theme'] == 'dark'


def test_optional_literal_disabled():
    def func(theme: Literal['light', 'dark'] | None): 
        pass
    
    params = analyze(func)
    form_data = {'theme': 'dark'}
    
    validated = validate_params(form_data, params)
    
    assert validated['theme'] is None


def test_optional_color_enabled():
    def func(color: Color | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'color': '#ff0000',
        'color_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['color'] == '#ff0000'


def test_optional_color_disabled():
    def func(color: Color | None): 
        pass
    
    params = analyze(func)
    form_data = {'color': '#ff0000'}
    
    validated = validate_params(form_data, params)
    
    assert validated['color'] is None


def test_optional_email_enabled():
    def func(email: Email | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'email': 'test@example.com',
        'email_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['email'] == 'test@example.com'


def test_optional_email_disabled():
    def func(email: Email | None): 
        pass
    
    params = analyze(func)
    form_data = {'email': 'test@example.com'}
    
    validated = validate_params(form_data, params)
    
    assert validated['email'] is None


def test_multiple_parameters_mixed():
    def func(
        name: str,
        age: int,
        active: bool,
        email: Email | None
    ): 
        pass
    
    params = analyze(func)
    form_data = {
        'name': 'John',
        'age': '25',
        'active': 'on',
        'email': 'john@example.com',
        'email_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['name'] == 'John'
    assert validated['age'] == 25
    assert validated['active'] is True
    assert validated['email'] == 'john@example.com'


def test_multiple_optionals_some_enabled():
    def func(
        opt1: int | None,
        opt2: str | None,
        opt3: bool | None
    ): 
        pass
    
    params = analyze(func)
    form_data = {
        'opt1': '42',
        'opt1_optional_toggle': 'on',
        'opt2': 'hello',
        # opt2 toggle missing - disabled
        'opt3': 'on',
        'opt3_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['opt1'] == 42
    assert validated['opt2'] is None
    assert validated['opt3'] is True


def test_complex_function_all_features():
    def func(
        name: str,
        age: Annotated[int, Field(ge=18, le=100)],
        score: float,
        active: bool,
        theme: Literal['light', 'dark'],
        color: Color,
        email: Email | None,
        bio: str | None
    ): 
        pass
    
    params = analyze(func)
    form_data = {
        'name': 'John',
        'age': '25',
        'score': '9.5',
        'active': 'on',
        'theme': 'dark',
        'color': '#f00',
        'email': 'john@example.com',
        'email_optional_toggle': 'on',
        'bio': 'Hello world',
        'bio_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['name'] == 'John'
    assert validated['age'] == 25
    assert validated['score'] == 9.5
    assert validated['active'] is True
    assert validated['theme'] == 'dark'
    assert validated['color'] == '#ff0000'  # Expanded from #f00
    assert validated['email'] == 'john@example.com'
    assert validated['bio'] == 'Hello world'


def test_all_optionals_disabled():
    def func(
        opt1: int | None,
        opt2: str | None,
        opt3: bool | None
    ): 
        pass
    
    params = analyze(func)
    form_data = {
        'opt1': '42',
        'opt2': 'hello',
        'opt3': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['opt1'] is None
    assert validated['opt2'] is None
    assert validated['opt3'] is None


def test_hex_color_uppercase():
    def func(color: Color): 
        pass
    
    params = analyze(func)
    form_data = {'color': '#FF0000'}
    
    validated = validate_params(form_data, params)
    
    assert validated['color'] == '#FF0000'


def test_hex_color_mixed_case():
    def func(color: Color): 
        pass
    
    params = analyze(func)
    form_data = {'color': '#fF00Aa'}
    
    validated = validate_params(form_data, params)
    
    assert validated['color'] == '#fF00Aa'


def test_empty_string_for_optional_type():
    def func(name: str | None): 
        pass
    
    params = analyze(func)
    form_data = {
        'name': '',
        'name_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['name'] is None


def test_literal_with_numeric_string_types():
    def func(size: Literal[1, 2, 3]): 
        pass
    
    params = analyze(func)
    form_data = {'size': '3'}
    
    validated = validate_params(form_data, params)
    
    assert validated['size'] == 3
    assert type(validated['size']) is int


def test_date_invalid_format_raises():
    def func(birthday: date): 
        pass
    
    params = analyze(func)
    form_data = {'birthday': '01/01/2000'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_time_invalid_format_raises():
    def func(meeting: time): 
        pass
    
    params = analyze(func)
    form_data = {'meeting': '2:30 PM'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_int_invalid_string_raises():
    def func(age: int): 
        pass
    
    params = analyze(func)
    form_data = {'age': 'twenty'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_float_invalid_string_raises():
    def func(price: float): 
        pass
    
    params = analyze(func)
    form_data = {'price': 'nine-ninety-nine'}
    
    with pytest.raises(ValueError):
        validate_params(form_data, params)


def test_empty_form_data():
    def func(x: int): 
        pass
    
    params = analyze(func)
    form_data = {}
    
    # When a required field is missing, validate_params returns None
    # The actual error will happen when calling the function
    validated = validate_params(form_data, params)
    
    assert validated['x'] is None


def test_negative_integers():
    def func(x: int): 
        pass
    
    params = analyze(func)
    form_data = {'x': '-42'}
    
    validated = validate_params(form_data, params)
    
    assert validated['x'] == -42


def test_negative_floats():
    def func(price: float): 
        pass
    
    params = analyze(func)
    form_data = {'price': '-9.99'}
    
    validated = validate_params(form_data, params)
    
    assert validated['price'] == -9.99


def test_zero_values():
    def func(x: int, y: float): 
        pass
    
    params = analyze(func)
    form_data = {'x': '0', 'y': '0.0'}
    
    validated = validate_params(form_data, params)
    
    assert validated['x'] == 0
    assert validated['y'] == 0.0


def test_very_large_numbers():
    def func(x: int, y: float): 
        pass
    
    params = analyze(func)
    form_data = {'x': '999999999', 'y': '999999999.999'}
    
    validated = validate_params(form_data, params)
    
    assert validated['x'] == 999999999
    assert validated['y'] == 999999999.999


def test_scientific_notation_float():
    def func(value: float): 
        pass
    
    params = analyze(func)
    form_data = {'value': '1.5e10'}
    
    validated = validate_params(form_data, params)
    
    assert validated['value'] == 1.5e10


def test_date_edge_cases():
    def func(d1: date, d2: date, d3: date): 
        pass
    
    params = analyze(func)
    form_data = {
        'd1': '2000-01-01',  # Start of century
        'd2': '2024-12-31',  # End of year
        'd3': '2024-02-29'   # Leap year
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['d1'] == date(2000, 1, 1)
    assert validated['d2'] == date(2024, 12, 31)
    assert validated['d3'] == date(2024, 2, 29)


def test_time_edge_cases():
    def func(t1: time, t2: time, t3: time): 
        pass
    
    params = analyze(func)
    form_data = {
        't1': '00:00',  # Midnight
        't2': '23:59',  # End of day
        't3': '12:00'   # Noon
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['t1'] == time(0, 0)
    assert validated['t2'] == time(23, 59)
    assert validated['t3'] == time(12, 0)


def test_time_with_seconds():
    def func(meeting: time): 
        pass
    
    params = analyze(func)
    form_data = {'meeting': '14:30:45'}
    
    validated = validate_params(form_data, params)
    
    assert validated['meeting'] == time(14, 30, 45)


def test_whitespace_in_strings():
    def func(name: str): 
        pass
    
    params = analyze(func)
    form_data = {'name': '  spaces around  '}
    
    validated = validate_params(form_data, params)
    
    assert validated['name'] == '  spaces around  '


def test_special_characters_in_strings():
    def func(text: str): 
        pass
    
    params = analyze(func)
    form_data = {'text': 'Hello!@#$%^&*()_+-=[]{}|;:,.<>?'}
    
    validated = validate_params(form_data, params)
    
    assert validated['text'] == 'Hello!@#$%^&*()_+-=[]{}|;:,.<>?'


def test_unicode_characters():
    def func(text: str): 
        pass
    
    params = analyze(func)
    form_data = {'text': 'Héllo 世界 🌍'}
    
    validated = validate_params(form_data, params)
    
    assert validated['text'] == 'Héllo 世界 🌍'


def test_newlines_in_strings():
    def func(text: str): 
        pass
    
    params = analyze(func)
    form_data = {'text': 'Line 1\nLine 2\nLine 3'}
    
    validated = validate_params(form_data, params)
    
    assert validated['text'] == 'Line 1\nLine 2\nLine 3'


def test_empty_string_for_required_str():
    def func(name: str): 
        pass
    
    params = analyze(func)
    form_data = {'name': ''}
    
    validated = validate_params(form_data, params)
    
    # Empty string should convert to None
    assert validated['name'] is None


def test_color_lowercase_letters():
    def func(color: Color): 
        pass
    
    params = analyze(func)
    form_data = {'color': '#abc'}
    
    validated = validate_params(form_data, params)
    
    assert validated['color'] == '#aabbcc'


def test_color_uppercase_letters():
    def func(color: Color): 
        pass
    
    params = analyze(func)
    form_data = {'color': '#ABC'}
    
    validated = validate_params(form_data, params)
    
    assert validated['color'] == '#AABBCC'


def test_email_various_formats():
    def func(e1: Email, e2: Email, e3: Email): 
        pass
    
    params = analyze(func)
    form_data = {
        'e1': 'user@example.com',
        'e2': 'user.name+tag@example.co.uk',
        'e3': 'user123@sub.example.com'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['e1'] == 'user@example.com'
    assert validated['e2'] == 'user.name+tag@example.co.uk'
    assert validated['e3'] == 'user123@sub.example.com'


def test_literal_empty_string():
    def func(choice: Literal['', 'a', 'b']): 
        pass
    
    params = analyze(func)
    form_data = {'choice': ''}
    
    validated = validate_params(form_data, params)
    
    assert validated['choice'] == ''


def test_float_with_leading_zero():
    def func(value: float): 
        pass
    
    params = analyze(func)
    form_data = {'value': '0.5'}
    
    validated = validate_params(form_data, params)
    
    assert validated['value'] == 0.5


def test_float_without_leading_zero():
    def func(value: float): 
        pass
    
    params = analyze(func)
    form_data = {'value': '.5'}
    
    validated = validate_params(form_data, params)
    
    assert validated['value'] == 0.5


def test_int_with_leading_zeros():
    def func(x: int): 
        pass
    
    params = analyze(func)
    form_data = {'x': '00042'}
    
    validated = validate_params(form_data, params)
    
    assert validated['x'] == 42


def test_constraints_at_exact_boundaries():
    def func(
        age: Annotated[int, Field(ge=18, le=100)]
    ): 
        pass
    
    params = analyze(func)
    
    # Test lower boundary
    form_data = {'age': '18'}
    validated = validate_params(form_data, params)
    assert validated['age'] == 18
    
    # Test upper boundary
    form_data = {'age': '100'}
    validated = validate_params(form_data, params)
    assert validated['age'] == 100


def test_gt_lt_at_boundaries():
    def func(
        rating: Annotated[float, Field(gt=0, lt=5)]
    ): 
        pass
    
    params = analyze(func)
    
    # Just above lower boundary - should pass
    form_data = {'rating': '0.01'}
    validated = validate_params(form_data, params)
    assert validated['rating'] == 0.01
    
    # Just below upper boundary - should pass
    form_data = {'rating': '4.99'}
    validated = validate_params(form_data, params)
    assert validated['rating'] == 4.99


def test_string_length_at_boundaries():
    def func(
        text: Annotated[str, Field(min_length=5, max_length=10)]
    ): 
        pass
    
    params = analyze(func)
    
    # Exactly min length
    form_data = {'text': 'hello'}
    validated = validate_params(form_data, params)
    assert validated['text'] == 'hello'
    
    # Exactly max length
    form_data = {'text': 'helloworld'}
    validated = validate_params(form_data, params)
    assert validated['text'] == 'helloworld'


def test_multiple_dynamic_literals():
    def get_options1():
        return ['A', 'B']
    
    def get_options2():
        return [1, 2, 3]
    
    def func(
        choice1: Literal[get_options1],
        choice2: Literal[get_options2]
    ): 
        pass
    
    params = analyze(func)
    
    # Both can have any value since they're dynamic
    form_data = {
        'choice1': 'Z',
        'choice2': '99'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['choice1'] == 'Z'
    assert validated['choice2'] == 99


def test_bool_various_truthy_values():
    def func(b1: bool, b2: bool, b3: bool): 
        pass
    
    params = analyze(func)
    
    # Only 'on' presence matters, value doesn't
    form_data = {
        'b1': 'on',
        'b2': 'true',
        'b3': '1'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['b1'] is True
    assert validated['b2'] is True
    assert validated['b3'] is True


def test_optional_with_empty_string_vs_none():
    def func(text: str | None): 
        pass
    
    params = analyze(func)
    
    # When toggle is on but value is empty, should be None
    form_data = {
        'text': '',
        'text_optional_toggle': 'on'
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['text'] is None


def test_all_parameters_types_in_one_function():
    def get_modes():
        return ['fast', 'slow']
    
    def func(
        # Required types
        req_int: int,
        req_float: float,
        req_str: str,
        req_bool: bool,
        req_date: date,
        req_time: time,
        
        # Annotated types
        ann_int: Annotated[int, Field(ge=0)],
        ann_str: Annotated[str, Field(min_length=3)],
        
        # Special types
        color: Color,
        email: Email,
        
        # Literals
        lit_static: Literal['a', 'b'],
        lit_dynamic: Literal[get_modes],
        
        # Optionals
        opt_int: int | None,
        opt_str: str | None,
        opt_bool: bool | None,
        opt_ann: Annotated[int, Field(ge=0)] | None,
        opt_color: Color | None,
        opt_lit: Literal['x', 'y'] | None,
    ): 
        pass
    
    params = analyze(func)
    
    form_data = {
        'req_int': '42',
        'req_float': '3.14',
        'req_str': 'hello',
        'req_bool': 'on',
        'req_date': '2024-01-01',
        'req_time': '14:30',
        'ann_int': '10',
        'ann_str': 'test',
        'color': '#f00',
        'email': 'test@example.com',
        'lit_static': 'a',
        'lit_dynamic': 'fast',
        'opt_int': '99',
        'opt_int_optional_toggle': 'on',
        'opt_str': 'text',
        'opt_str_optional_toggle': 'on',
        'opt_bool': 'on',
        'opt_bool_optional_toggle': 'on',
        'opt_ann': '5',
        'opt_ann_optional_toggle': 'on',
        'opt_color': '#00f',
        'opt_color_optional_toggle': 'on',
        'opt_lit': 'x',
        'opt_lit_optional_toggle': 'on',
    }
    
    validated = validate_params(form_data, params)
    
    assert validated['req_int'] == 42
    assert validated['req_float'] == 3.14
    assert validated['req_str'] == 'hello'
    assert validated['req_bool'] is True
    assert validated['req_date'] == date(2024, 1, 1)
    assert validated['req_time'] == time(14, 30)
    assert validated['ann_int'] == 10
    assert validated['ann_str'] == 'test'
    assert validated['color'] == '#ff0000'
    assert validated['email'] == 'test@example.com'
    assert validated['lit_static'] == 'a'
    assert validated['lit_dynamic'] == 'fast'
    assert validated['opt_int'] == 99
    assert validated['opt_str'] == 'text'
    assert validated['opt_bool'] is True
    assert validated['opt_ann'] == 5
    assert validated['opt_color'] == '#0000ff'
    assert validated['opt_lit'] == 'x'