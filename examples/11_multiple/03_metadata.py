from func_to_web import run, FunctionMetadata

def double(x: int):
    return x * 2

def half(x: int):
    return x / 2

run([
    FunctionMetadata(
        function=double,
        name="Double a number",
        description="Multiplies the input by 2",
    ),
    FunctionMetadata(
        function=half,
        name="Half a number",
        description="Divides the input by 2",
    ),
])
