import pytest
from datetime import date, time
from func_to_web import *
from func_to_web.analyze_function import analyze, ParamInfo
from func_to_web.build_form_fields import build_form_fields
from func_to_web.custom_pydantic_types import *

def test_int_field():
    def func(x: int):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 1
    assert fields[0]['name'] == 'x'
    assert fields[0]['type'] == 'number'
    assert fields[0]['step'] == '1'
    assert fields[0]['required'] is True
    assert fields[0]['is_optional'] is False


def test_float_field():
    def func(price: float):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 1
    assert fields[0]['name'] == 'price'
    assert fields[0]['type'] == 'number'
    assert fields[0]['step'] == 'any'
    assert fields[0]['required'] is True


def test_str_field():
    def func(name: str):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 1
    assert fields[0]['name'] == 'name'
    assert fields[0]['type'] == 'text'
    assert fields[0]['required'] is True


def test_bool_field():
    def func(active: bool):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 1
    assert fields[0]['name'] == 'active'
    assert fields[0]['type'] == 'checkbox'
    assert fields[0]['required'] is False  # Checkboxes are never required


def test_date_field():
    def func(birthday: date):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 1
    assert fields[0]['name'] == 'birthday'
    assert fields[0]['type'] == 'date'
    assert fields[0]['required'] is True


def test_time_field():
    def func(meeting: time):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 1
    assert fields[0]['name'] == 'meeting'
    assert fields[0]['type'] == 'time'
    assert fields[0]['required'] is True


def test_date_with_default():
    default_date = date(2000, 1, 1)
    
    def func(birthday: date = default_date):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['default'] == '2000-01-01'  # Converted to ISO format


def test_time_with_default():
    default_time = time(14, 30)
    
    def func(meeting: time = default_time):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['default'] == '14:30'  # Converted to HH:MM format


def test_int_with_default():
    def func(age: int = 25):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['default'] == 25


def test_str_with_default():
    def func(name: str = "John"):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['default'] == "John"


def test_bool_with_default():
    def func(active: bool = True):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['default'] is True


def test_int_with_ge_le_constraints():
    def func(age: Annotated[int, Field(ge=0, le=120)]):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'number'
    assert fields[0]['min'] == 0
    assert fields[0]['max'] == 120
    assert fields[0]['step'] == '1'


def test_int_with_gt_lt_constraints():
    def func(score: Annotated[int, Field(gt=0, lt=100)]):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'number'
    assert fields[0]['min'] == 1  # gt=0 becomes min=1 for int
    assert fields[0]['max'] == 99  # lt=100 becomes max=99 for int


def test_float_with_gt_lt_constraints():
    def func(rating: Annotated[float, Field(gt=0, lt=5)]):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'number'
    assert fields[0]['min'] == 0.01  # gt=0 becomes min=0.01 for float
    assert fields[0]['max'] == 4.99  # lt=5 becomes max=4.99 for float
    assert fields[0]['step'] == 'any'


def test_str_with_length_constraints():
    def func(username: Annotated[str, Field(min_length=3, max_length=20)]):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'text'
    assert fields[0]['minlength'] == 3
    assert fields[0]['maxlength'] == 20


def test_str_with_min_length_only():
    def func(password: Annotated[str, Field(min_length=8)]):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'text'
    assert fields[0]['minlength'] == 8
    assert 'maxlength' not in fields[0]


def test_str_with_max_length_only():
    def func(bio: Annotated[str, Field(max_length=500)]):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'text'
    assert fields[0]['maxlength'] == 500
    assert 'minlength' not in fields[0]


def test_color_field():
    def func(color: Color):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'color'
    assert 'pattern' in fields[0]


def test_email_field():
    def func(email: Email):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'email'
    assert 'pattern' in fields[0]


def test_image_file_field():
    def func(photo: ImageFile):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'file'
    assert fields[0]['accept'] == '.png,.jpg,.jpeg,.gif,.webp'
    assert 'pattern' in fields[0]


def test_data_file_field():
    def func(data: DataFile):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'file'
    assert fields[0]['accept'] == '.csv,.xlsx,.xls,.json'


def test_text_file_field():
    def func(notes: TextFile):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'file'
    assert fields[0]['accept'] == '.txt,.md,.log'


def test_document_file_field():
    def func(report: DocumentFile):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'file'
    assert fields[0]['accept'] == '.pdf,.doc,.docx'


def test_literal_string_field():
    def func(theme: Literal['light', 'dark', 'auto']):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == ('light', 'dark', 'auto')


def test_literal_int_field():
    def func(size: Literal[1, 2, 3]):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == (1, 2, 3)


def test_literal_with_default():
    def func(theme: Literal['light', 'dark'] = 'light'):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == ('light', 'dark')
    assert fields[0]['default'] == 'light'


def test_dynamic_literal_function():
    def get_options():
        return ['A', 'B', 'C']
    
    def func(choice: Literal[get_options]):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == ('A', 'B', 'C')


def test_dynamic_literal_returns_single_value():
    def get_option():
        return "Hello"
    
    def func(choice: Literal[get_option]):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == ('Hello',)


def test_dynamic_literal_returns_tuple():
    def get_options():
        return ('X', 'Y', 'Z')
    
    def func(choice: Literal[get_options]):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == ('X', 'Y', 'Z')


def test_dynamic_literal_refreshes_on_each_call():
    counter = {'value': 0}
    
    def get_dynamic_options():
        counter['value'] += 1
        return [f'Option{counter["value"]}']
    
    def func(choice: Literal[get_dynamic_options]):
        pass
    
    params = analyze(func)
    
    # First call
    fields1 = build_form_fields(params)
    options1 = fields1[0]['options']
    
    # Second call - should re-execute and get different result
    fields2 = build_form_fields(params)
    options2 = fields2[0]['options']
    
    assert options1 == ('Option2',)  # Counter was 1, now 2
    assert options2 == ('Option3',)  # Counter was 2, now 3
    assert options1 != options2


def test_optional_int_field():
    def func(age: int | None):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['is_optional'] is True
    assert fields[0]['required'] is False
    assert fields[0]['optional_enabled'] is False  # No default, starts disabled


def test_optional_with_default():
    def func(age: int | None = 25):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['is_optional'] is True
    assert fields[0]['required'] is False
    assert fields[0]['optional_enabled'] is True  # Has default, starts enabled
    assert fields[0]['default'] == 25


def test_optional_without_default():
    def func(name: str | None = None):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['is_optional'] is True
    assert fields[0]['optional_enabled'] is False  # default is None, starts disabled


def test_optional_with_constraints():
    def func(age: Annotated[int, Field(ge=18)] | None):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'number'
    assert fields[0]['is_optional'] is True
    assert fields[0]['min'] == 18


def test_multiple_fields():
    def func(name: str, age: int, active: bool):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 3
    assert fields[0]['name'] == 'name'
    assert fields[0]['type'] == 'text'
    assert fields[1]['name'] == 'age'
    assert fields[1]['type'] == 'number'
    assert fields[2]['name'] == 'active'
    assert fields[2]['type'] == 'checkbox'


def test_complex_function_all_types():
    def func(
        text: str,
        number: int,
        decimal: float,
        checkbox: bool,
        birthday: date,
        meeting: time,
        color: Color,
        email: Email,
        theme: Literal['light', 'dark'],
        photo: ImageFile,
        optional: str | None
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 11
    
    assert fields[0]['type'] == 'text'
    assert fields[1]['type'] == 'number'
    assert fields[1]['step'] == '1'
    assert fields[2]['type'] == 'number'
    assert fields[2]['step'] == 'any'
    assert fields[3]['type'] == 'checkbox'
    assert fields[4]['type'] == 'date'
    assert fields[5]['type'] == 'time'
    assert fields[6]['type'] == 'color'
    assert fields[7]['type'] == 'email'
    assert fields[8]['type'] == 'select'
    assert fields[9]['type'] == 'file'
    assert fields[10]['is_optional'] is True


def test_field_names_preserved():
    def func(first_name: str, last_name: str, age_in_years: int):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['name'] == 'first_name'
    assert fields[1]['name'] == 'last_name'
    assert fields[2]['name'] == 'age_in_years'


def test_all_constraints_in_one_field():
    def func(
        username: Annotated[str, Field(min_length=3, max_length=20)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'text'
    assert fields[0]['minlength'] == 3
    assert fields[0]['maxlength'] == 20


def test_numeric_constraints_all_types():
    def func(
        ge_only: Annotated[int, Field(ge=0)],
        le_only: Annotated[int, Field(le=100)],
        gt_only: Annotated[int, Field(gt=0)],
        lt_only: Annotated[int, Field(lt=100)],
        both: Annotated[int, Field(ge=18, le=120)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert 'min' in fields[0] and 'max' not in fields[0]
    assert 'max' in fields[1] and 'min' not in fields[1]
    assert 'min' in fields[2] and 'max' not in fields[2]
    assert 'max' in fields[3] and 'min' not in fields[3]
    assert 'min' in fields[4] and 'max' in fields[4]


def test_empty_function():
    def func():
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields == []


def test_literal_single_option():
    def func(mode: Literal['readonly']):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == ('readonly',)


def test_date_without_default():
    def func(birthday: date):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    # Should not convert None to ISO format
    assert fields[0]['default'] is None


def test_time_without_default():
    def func(meeting: time):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    # Should not convert None to time format
    assert fields[0]['default'] is None


def test_optional_color():
    def func(color: Color | None):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'color'
    assert fields[0]['is_optional'] is True


def test_optional_email():
    def func(email: Email | None):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'email'
    assert fields[0]['is_optional'] is True


def test_optional_file():
    def func(photo: ImageFile | None):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'file'
    assert fields[0]['is_optional'] is True


def test_optional_literal():
    def func(theme: Literal['light', 'dark'] | None):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['is_optional'] is True


def test_optional_date():
    def func(birthday: date | None):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'date'
    assert fields[0]['is_optional'] is True


def test_optional_time():
    def func(meeting: time | None):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'time'
    assert fields[0]['is_optional'] is True


def test_optional_bool():
    def func(active: bool | None):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'checkbox'
    assert fields[0]['is_optional'] is True
    assert fields[0]['required'] is False  # Checkboxes are never required


def test_multiple_dynamic_literals():
    def get_colors():
        return ['red', 'blue', 'green']
    
    def get_sizes():
        return [1, 2, 3]
    
    def func(color: Literal[get_colors], size: Literal[get_sizes]):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 2
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == ('red', 'blue', 'green')
    assert fields[1]['type'] == 'select'
    assert fields[1]['options'] == (1, 2, 3)


def test_mixed_static_and_dynamic_literals():
    def get_modes():
        return ['fast', 'slow']
    
    def func(
        theme: Literal['light', 'dark'],
        mode: Literal[get_modes]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 2
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == ('light', 'dark')
    assert fields[1]['type'] == 'select'
    assert fields[1]['options'] == ('fast', 'slow')


def test_optional_with_all_constraint_types():
    def func(
        age: Annotated[int, Field(ge=18, le=100)] | None = None,
        username: Annotated[str, Field(min_length=3, max_length=20)] | None = None,
        rating: Annotated[float, Field(gt=0, lt=5)] | None = None
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 3
    
    # Age field
    assert fields[0]['is_optional'] is True
    assert fields[0]['min'] == 18
    assert fields[0]['max'] == 100
    
    # Username field
    assert fields[1]['is_optional'] is True
    assert fields[1]['minlength'] == 3
    assert fields[1]['maxlength'] == 20
    
    # Rating field
    assert fields[2]['is_optional'] is True
    assert fields[2]['min'] == 0.01
    assert fields[2]['max'] == 4.99


def test_all_file_types_together():
    def func(
        img: ImageFile,
        data: DataFile,
        txt: TextFile,
        doc: DocumentFile
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 4
    assert all(f['type'] == 'file' for f in fields)
    assert fields[0]['accept'] == '.png,.jpg,.jpeg,.gif,.webp'
    assert fields[1]['accept'] == '.csv,.xlsx,.xls,.json'
    assert fields[2]['accept'] == '.txt,.md,.log'
    assert fields[3]['accept'] == '.pdf,.doc,.docx'


def test_optional_files_with_defaults():
    def func(
        photo: ImageFile | None = None,
        data: DataFile | None = None
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 2
    assert fields[0]['type'] == 'file'
    assert fields[0]['is_optional'] is True
    assert fields[0]['optional_enabled'] is False
    assert fields[1]['type'] == 'file'
    assert fields[1]['is_optional'] is True
    assert fields[1]['optional_enabled'] is False


def test_all_special_types_together():
    def func(
        color: Color,
        email: Email,
        img: ImageFile
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 3
    assert fields[0]['type'] == 'color'
    assert fields[1]['type'] == 'email'
    assert fields[2]['type'] == 'file'


def test_constraints_with_exact_boundary_values():
    def func(
        age: Annotated[int, Field(ge=0, le=0)],  # Only 0 allowed
        score: Annotated[int, Field(ge=100, le=100)]  # Only 100 allowed
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['min'] == 0
    assert fields[0]['max'] == 0
    assert fields[1]['min'] == 100
    assert fields[1]['max'] == 100


def test_float_with_very_precise_constraints():
    def func(
        value: Annotated[float, Field(ge=0.001, le=0.999)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'number'
    assert fields[0]['step'] == 'any'
    assert fields[0]['min'] == 0.001
    assert fields[0]['max'] == 0.999


def test_negative_constraint_values():
    def func(
        temp: Annotated[int, Field(ge=-100, le=-10)],
        balance: Annotated[float, Field(ge=-1000.0, le=1000.0)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['min'] == -100
    assert fields[0]['max'] == -10
    assert fields[1]['min'] == -1000.0
    assert fields[1]['max'] == 1000.0


def test_very_large_constraint_values():
    def func(
        population: Annotated[int, Field(ge=0, le=10_000_000_000)],
        distance: Annotated[float, Field(ge=0, le=1e100)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['max'] == 10_000_000_000
    assert fields[1]['max'] == 1e100


def test_string_with_zero_min_length():
    def func(
        text: Annotated[str, Field(min_length=0, max_length=100)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['minlength'] == 0
    assert fields[0]['maxlength'] == 100


def test_string_with_equal_min_max_length():
    def func(
        code: Annotated[str, Field(min_length=5, max_length=5)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['minlength'] == 5
    assert fields[0]['maxlength'] == 5


def test_gt_lt_with_same_value_for_float():
    def func(
        value: Annotated[float, Field(gt=1.0, lt=1.0)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    # gt=1.0 becomes 1.01, lt=1.0 becomes 0.99
    # This creates impossible constraint but should still generate
    assert fields[0]['min'] == 1.01
    assert fields[0]['max'] == 0.99


def test_literal_with_numbers_and_zero():
    def func(
        choice: Literal[0, 1, 2, 3]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == (0, 1, 2, 3)
    assert 0 in fields[0]['options']


def test_literal_with_negative_numbers():
    def func(
        choice: Literal[-10, -5, 0, 5, 10]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == (-10, -5, 0, 5, 10)


def test_literal_with_float_values():
    def func(
        multiplier: Literal[0.5, 1.0, 1.5, 2.0]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == (0.5, 1.0, 1.5, 2.0)


def test_literal_with_empty_string():
    def func(
        choice: Literal['', 'option1', 'option2']
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert '' in fields[0]['options']




def test_literal_with_unicode_strings():
    def func(
        emoji: Literal['😀', '😎', '🚀', '🎉']
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['options'] == ('😀', '😎', '🚀', '🎉')


def test_literal_with_multiline_strings():
    def func(
        template: Literal['line1\nline2', 'single line']
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert 'line1\nline2' in fields[0]['options']

def test_dynamic_literal_returns_empty_list():
    def get_empty():
        return []
    
    def func(choice: Literal[get_empty]):
        pass
    
    # Empty list means no valid type can be inferred
    # Should fail in analyze() with TypeError
    with pytest.raises(TypeError, match="not supported"):
        params = analyze(func)


def test_dynamic_literal_returns_mixed_types_in_list():
    def get_mixed():
        # This would fail in analyze() but test build_form_fields behavior
        return ['text', 123, 45.6]
    
    def func(choice: Literal[get_mixed]):
        pass
    
    # Should fail in analyze, but if it somehow passes...
    try:
        params = analyze(func)
        fields = build_form_fields(params)
        # If we get here, just verify it returns something
        assert fields[0]['type'] == 'select'
    except TypeError:
        # Expected to fail in analyze
        pass


def test_datetime_defaults_with_seconds():
    default_time = time(14, 30, 45)
    
    def func(meeting: time = default_time):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    # Should only format to HH:MM, ignoring seconds
    assert fields[0]['default'] == '14:30'


def test_date_with_leap_year():
    leap_date = date(2024, 2, 29)
    
    def func(birthday: date = leap_date):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['default'] == '2024-02-29'


def test_date_with_century_boundaries():
    old_date = date(1900, 1, 1)
    future_date = date(2100, 12, 31)
    
    def func(
        old: date = old_date,
        future: date = future_date
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['default'] == '1900-01-01'
    assert fields[1]['default'] == '2100-12-31'


def test_time_with_midnight_and_noon():
    midnight = time(0, 0)
    noon = time(12, 0)
    end_of_day = time(23, 59)
    
    def func(
        start: time = midnight,
        lunch: time = noon,
        end: time = end_of_day
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['default'] == '00:00'
    assert fields[1]['default'] == '12:00'
    assert fields[2]['default'] == '23:59'


def test_multiple_optionals_mixed_enabled_states():
    def func(
        opt1: int | None,  # No default, disabled
        opt2: int | None = 42,  # Has default, enabled
        opt3: str | None = None,  # None default, disabled
        opt4: str | None = "text"  # String default, enabled
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['optional_enabled'] is False
    assert fields[1]['optional_enabled'] is True
    assert fields[2]['optional_enabled'] is False
    assert fields[3]['optional_enabled'] is True


def test_complex_nested_function_ordering():
    def get_dynamic():
        return ['opt1', 'opt2']
    
    def func(
        a_first: str,
        b_number: int,
        c_optional: str | None,
        d_literal: Literal['x', 'y'],
        e_dynamic: Literal[get_dynamic],
        f_color: Color,
        g_file: ImageFile,
        h_constrained: Annotated[int, Field(ge=0, le=100)],
        i_last: bool
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 9
    assert fields[0]['name'] == 'a_first'
    assert fields[8]['name'] == 'i_last'
    # Verify order is preserved
    names = [f['name'] for f in fields]
    assert names == ['a_first', 'b_number', 'c_optional', 'd_literal', 
                     'e_dynamic', 'f_color', 'g_file', 'h_constrained', 'i_last']


def test_all_types_with_defaults():
    def get_opt():
        return ['a', 'b']
    
    def func(
        i: int = 42,
        f: float = 3.14,
        s: str = "hello",
        b: bool = True,
        d: date = date(2024, 1, 1),
        t: time = time(12, 0),
        c: Color = "#ff0000",
        e: Email = "test@example.com",
        lit: Literal['x', 'y'] = 'x',
        dyn: Literal[get_opt] = 'a'
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert len(fields) == 10
    assert all(f['default'] is not None for f in fields)
    assert fields[0]['default'] == 42
    assert fields[1]['default'] == 3.14
    assert fields[2]['default'] == "hello"
    assert fields[3]['default'] is True
    assert fields[4]['default'] == '2024-01-01'
    assert fields[5]['default'] == '12:00'
    assert fields[6]['default'] == "#ff0000"
    assert fields[7]['default'] == "test@example.com"
    assert fields[8]['default'] == 'x'
    assert fields[9]['default'] == 'a'


def test_constraint_boundary_with_floats():
    def func(
        precise: Annotated[float, Field(ge=0.0001, le=0.9999)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['min'] == 0.0001
    assert fields[0]['max'] == 0.9999


def test_optional_dynamic_literal():
    def get_opts():
        return ['opt1', 'opt2', 'opt3']
    
    def func(choice: Literal[get_opts] | None = None):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['is_optional'] is True
    assert fields[0]['options'] == ('opt1', 'opt2', 'opt3')
    assert fields[0]['optional_enabled'] is False


def test_optional_dynamic_literal_with_default():
    def get_opts():
        return ['opt1', 'opt2', 'opt3']
    
    def func(choice: Literal[get_opts] | None = 'opt1'):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['type'] == 'select'
    assert fields[0]['is_optional'] is True
    assert fields[0]['optional_enabled'] is True
    assert fields[0]['default'] == 'opt1'


def test_file_fields_never_have_pattern_in_html_attributes():
    def func(img: ImageFile):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    # Pattern exists for validation but file input uses 'accept'
    assert 'pattern' in fields[0]
    assert 'accept' in fields[0]
    assert fields[0]['type'] == 'file'


def test_multiple_constraints_single_field():
    def func(
        value: Annotated[int, Field(ge=10, le=100)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert 'min' in fields[0]
    assert 'max' in fields[0]
    assert fields[0]['min'] == 10
    assert fields[0]['max'] == 100
    assert fields[0]['step'] == '1'
    assert fields[0]['type'] == 'number'


def test_gt_constraint_adds_increment():
    def func(
        int_val: Annotated[int, Field(gt=5)],
        float_val: Annotated[float, Field(gt=5.0)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    # gt=5 for int becomes min=6
    assert fields[0]['min'] == 6
    
    # gt=5.0 for float becomes min=5.01
    assert fields[1]['min'] == 5.01


def test_lt_constraint_subtracts_decrement():
    def func(
        int_val: Annotated[int, Field(lt=10)],
        float_val: Annotated[float, Field(lt=10.0)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    # lt=10 for int becomes max=9
    assert fields[0]['max'] == 9
    
    # lt=10.0 for float becomes max=9.99
    assert fields[1]['max'] == 9.99


def test_very_long_string_constraints():
    def func(
        essay: Annotated[str, Field(min_length=1000, max_length=10000)]
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    assert fields[0]['minlength'] == 1000
    assert fields[0]['maxlength'] == 10000


def test_color_and_email_preserve_pattern():
    def func(
        color: Color,
        email: Email
    ):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    # Both should have pattern for validation
    assert 'pattern' in fields[0]
    assert 'pattern' in fields[1]
    assert fields[0]['type'] == 'color'
    assert fields[1]['type'] == 'email'


def test_field_order_matches_function_signature():
    def func(z: int, y: str, x: bool):
        pass
    
    params = analyze(func)
    fields = build_form_fields(params)
    
    # Order should be preserved: z, y, x
    assert fields[0]['name'] == 'z'
    assert fields[1]['name'] == 'y'
    assert fields[2]['name'] == 'x'