"""A modal opened for its answer, which runs itself on the way in.

autorun makes the page press its own submit button as soon as it is ready.
It is for the function you open to see something —a report, a file, a link—
rather than to fill anything in: call() would skip the button too, but it
hands back JSON and leaves you to draw the result. Serve it as a script or
point uvicorn at the module: uvicorn examples.fastapi.modal_autorun:app
"""

from datetime import date
from typing import Annotated

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from func_to_web import Download, Label, app_of

PREFIX = "/tools"

TITLE = "Reports"

TEMPLATE = """\
<!doctype html>
<html>
<body>
<button id="summary">This month</button>
<button id="chosen">March 2026</button>
<button id="named">Name it first</button>
<pre id="log"></pre>
<script type="module">
import { openModal } from "__PREFIX__/static/sdk.js";

const log = document.getElementById("log");

const write = (text) => { log.textContent += `${text}\\n`; };

document.getElementById("summary").addEventListener("click", () => {
    openModal("__PREFIX__/summary", {
        autorun: true,
        onResult: (outputs) => write(`ready: ${outputs[0].filename}`),
    });
});

document.getElementById("chosen").addEventListener("click", () => {
    openModal("__PREFIX__/report", {
        autorun: true,
        prefill: {month: "2026-03-01"},
        hidden: ["month"],
        onResult: (outputs) => write(`ready: ${outputs[0].filename}`),
    });
});

document.getElementById("named").addEventListener("click", () => {
    openModal("__PREFIX__/named_report", {
        autorun: true,
        onResult: (outputs) => write(`ready: ${outputs[0].filename}`),
    });
});
</script>
</body>
</html>
"""

PAGE = TEMPLATE.replace("__PREFIX__", PREFIX)


def summary() -> Annotated[bytes, Download("summary.txt")]:
    """Take no parameters at all, so there is nothing to fill in."""
    return b"Everything is fine.\n"


def report(
    month: Annotated[date, Label("Month")] = date(2026, 1, 1),
) -> Annotated[bytes, Download("report.txt")]:
    """Take a parameter the host prefills and hides."""
    return f"Report for {month:%B %Y}\n".encode()


def named_report(
    name: Annotated[str, Label("Report name")],
) -> Annotated[bytes, Download("named.txt")]:
    """Take a required parameter nobody filled: autorun leaves this alone."""
    return f"Report: {name}\n".encode()


SPACE = [summary, report, named_report]

app = FastAPI()

app.mount(PREFIX, app_of(SPACE, title=TITLE))


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Serve the host page that opens the modals."""
    return PAGE


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
