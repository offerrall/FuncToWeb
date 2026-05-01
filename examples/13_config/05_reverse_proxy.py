from func_to_web import run

def hello(name: str = "World"):
    return f"Hello, {name}!"

# Behind nginx at /tools/my-app/
run(hello, host="127.0.0.1", port=8000, root_path="/tools/my-app")
