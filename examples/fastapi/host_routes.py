"""A host application that keeps its own routes next to a mounted space.

The JSON API of the application and the pages of the space live in the same
FastAPI instance and share its middleware. Authentication and authorization
are the responsibility of the host application: FuncToWeb mounts an
ASGI application and inherits middleware wrapped around its mount. Serve it as a
script or point uvicorn at the module:
uvicorn examples.fastapi.host_routes:app
"""

from enum import Enum
from typing import Annotated

import uvicorn
from fastapi import FastAPI

from func_to_web import Label, Min, app_of


class Currency(Enum):
    """A currency the internal desk quotes against the euro."""

    USD = "usd"
    GBP = "gbp"
    JPY = "jpy"


RATES = {Currency.USD: 1.09, Currency.GBP: 0.85, Currency.JPY: 171.4}


def convert(
    amount: Annotated[float, Min(0.0), Label("Amount in euros")],
    currency: Currency = Currency.USD,
) -> str:
    """Convert an amount of euros using the fixed desk rates."""
    return f"{amount * RATES[currency]:.2f} {currency.value.upper()}"


app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the host application is alive."""
    return {"status": "ok"}


@app.get("/api/rates")
def rates() -> dict[str, float]:
    """Publish the same rates the mounted space uses."""
    return {code.value: rate for code, rate in RATES.items()}


app.mount("/tools", app_of([convert], title="Currency desk"))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
