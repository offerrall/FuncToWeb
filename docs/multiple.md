# Multiple Functions

Pass a list of functions to create an index page with navigation:

```python
from func_to_web import run

def calculate_bmi(weight_kg: float, height_m: float):
    """Calculate Body Mass Index"""
    return f"BMI: {weight_kg / (height_m ** 2):.2f}"

def celsius_to_fahrenheit(celsius: float):
    """Convert Celsius to Fahrenheit"""
    return f"{celsius}°C = {(celsius * 9/5) + 32}°F"

run([calculate_bmi, celsius_to_fahrenheit])
```

If only one visible function exists, the index page is skipped and it opens directly.

## Groups

Pass a dictionary to organize functions into collapsible groups:

```python
from func_to_web import run

def add(a: int, b: int): return a + b
def multiply(a: int, b: int): return a * b
def upper(text: str): return text.upper()
def lower(text: str): return text.lower()

run({
    "Math": [add, multiply],
    "Text": [upper, lower],
})
```

## Custom Name & Description

Use `FunctionMetadata` to override the auto-generated name and description:

```python
from func_to_web import run, FunctionMetadata

def my_func(x: int): return x * 2

run(FunctionMetadata(
    function=my_func,
    name="Double a number",
    description="Multiplies the input by 2",
))
```

By default, the name is derived from the function name (`my_func` → `My func`) and the description from its docstring.

## Hidden Functions

Use `HiddenFunction` to register a function without showing it in the index. It's still accessible via its URL — useful for two cases:

- Functions only reached via `ActionTable` row navigation
- Functions embedded as modal endpoints in an existing web app via iframe or URL prefill

```python
from func_to_web import run, HiddenFunction

def list_users(): ...
def edit_user(id: int, name: str): ...

run([list_users, HiddenFunction(edit_user)])
```

`edit_user` won't appear in the index but is reachable at `/edit-user` — directly or via `ActionTable`.

## Custom App Title

```python
run([func1, func2], app_title="My Internal Tools")
```