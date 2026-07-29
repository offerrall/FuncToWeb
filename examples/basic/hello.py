"""run() serves one typed function as a web form and nothing else."""

from func_to_web import run


def greet(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}! Welcome to FuncToWeb."


if __name__ == "__main__":
    run(greet, title="Hello")
