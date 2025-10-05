# pyright: reportInvalidTypeForm=false
from FuncToWeb import run
from FuncToWeb.ui_types import IntUi, StrUi, FloatUi, BoolUi

def FuncToWeb(int_param: IntUi(min=1, max=10),
              list_str_param: list[str] = ["Option 1", "Option 2", "Option 3"],
              str_param: StrUi(min_length=3, max_length=20) = "Hello",
              float_param: FloatUi(min=0.5, max=99.9) = 1.5,
              bool_param: BoolUi() = False):
    
    return f"Int: {int_param}, {type(int_param)}; " \
           f"List Str: {list_str_param}, {type(list_str_param)}; " \
           f"Str: {str_param}, {type(str_param)}; " \
           f"Float: {float_param}, {type(float_param)}; " \
           f"Bool: {bool_param}, {type(bool_param)}"

run(FuncToWeb)