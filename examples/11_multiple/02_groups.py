from func_to_web import run

def add(a: int, b: int): return a + b
def multiply(a: int, b: int): return a * b
def upper(text: str): return text.upper()
def reverse(text: str): return text[::-1]

run({
    "Math": [add, multiply],
    "Text": [upper, reverse],
}, app_title="My Tools")
