from func_to_web import run

def with_defaults(tags: list[str] = ["python", "web"]):
    return f"Tags: {tags}"

run(with_defaults)
