from func_to_web import run

def add(a: int, b: int): return a + b
def multiply(a: int, b: int): return a * b
def upper(text: str): return text.upper()
def reverse(text: str): return text[::-1]
def sin(x: float):
    import math
    return math.sin(x)

# Groups are dicts with exactly one key (the group name) and a list as value.
# That list can contain functions, FunctionMetadata, HiddenFunction, or more
# groups -- nesting is allowed and group dicts can be mixed with plain
# functions at any level.
run([
    {"Math": [
        add,
        multiply,
        {"Trig": [sin]},
    ]},
    {"Text": [upper, reverse]},
], app_title="My Tools")
