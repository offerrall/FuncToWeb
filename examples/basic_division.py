from func_to_web import run


def divide(a: float, b: float):
    return a / b # Division zero possible here, but handled by FuncToWeb

run(divide)