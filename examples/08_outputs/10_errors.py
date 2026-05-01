from func_to_web import run

def divide(a: float, b: float):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

run(divide)
