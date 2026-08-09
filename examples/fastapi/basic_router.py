"""A space of functions mounted on an application built by hand.

app_of() returns a Starlette/ASGI application: the host application is
created, configured and served by whoever writes it. Serve it as a script or
point uvicorn at the module: uvicorn examples.fastapi.basic_router:app
"""

import uvicorn
from fastapi import FastAPI

from func_to_web import app_of


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def divide(a: float, b: float = 1.0) -> float:
    """Divide the first number by the second one."""
    return a / b


def percentage(value: float, total: float) -> str:
    """Express a value as a percentage of a total."""
    return f"{value / total * 100:.2f} %"


app = FastAPI()

app.mount(
    "/tools",
    app_of([add, divide, percentage], title="Internal tools"),
)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
