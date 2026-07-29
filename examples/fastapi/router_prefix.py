"""The same router mounted under two different prefixes.

Every route of the router is relative, so the page, its static assets and its
invoke endpoints work under any prefix the host application chooses. The
prefix belongs to include_router(), not to router_of(). Serve it as a script
or point uvicorn at the module: uvicorn examples.fastapi.router_prefix:app
"""

import uvicorn
from fastapi import FastAPI

from func_to_web import router_of


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a temperature from Celsius to Fahrenheit."""
    return celsius * 9 / 5 + 32


def kilometres_to_miles(kilometres: float) -> float:
    """Convert a distance from kilometres to miles."""
    return kilometres * 0.621371


app = FastAPI()

conversions = router_of(
    [celsius_to_fahrenheit, kilometres_to_miles],
    title="Conversions",
)

app.include_router(conversions, prefix="/tools")
app.include_router(conversions, prefix="/v2/internal/tools")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
