"""A page of the host application that embeds a function in an iframe.

The page of a function is complete and self-contained, and the responses
carry no header that forbids embedding, so a host route can drop it into an
<iframe> without rebuilding the form. Everything is served by this same
application: no external resources are involved. Serve it as a script or
point uvicorn at the module: uvicorn examples.fastapi.iframe_host:app
"""

from datetime import date, timedelta

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from func_to_web import router_of

PAGE = """<h1>Support desk</h1>
<p>Estimate a delivery date without leaving this page.</p>
<iframe src="/tools/estimate-delivery/"
        title="Estimate delivery"
        width="100%"
        height="620"
        style="border: 1px solid rgba(128, 128, 128, 0.4)"></iframe>
"""


def estimate_delivery(distance_km: float, express: bool = False) -> str:
    """Estimate the delivery date for a distance in kilometres."""
    days = 1 + int(distance_km // 500)

    if not express:
        days += 2

    return f"Estimated delivery: {date.today() + timedelta(days=days)}"


app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """Serve the host page that embeds the function."""
    return PAGE


app.include_router(
    router_of([estimate_delivery], title="Support tools"),
    prefix="/tools",
)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
