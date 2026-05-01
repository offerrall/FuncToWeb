from func_to_web import run

def hello(name: str = "World"):
    return f"Hello, {name}!"

run(
    hello,
    css_vars={
        "--functoweb-submit-bg-light": "#10b981",
        "--functoweb-submit-bg-dark":  "#059669",
    },
)
