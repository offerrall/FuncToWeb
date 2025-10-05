from FuncToWeb import run
from FuncToWeb.ui_types import IntUi

def dividir(a: int, b: IntUi(min=1)): # type: ignore
    return a / b

run(dividir)