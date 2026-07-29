"""A frontend of your own calling the space through sdk.js.

sdk.js is a static asset of the space, so the page imports it straight from
the /static route it is mounted under: there is nothing to generate and no
route to add. Serve it as a script or point uvicorn at the module:
uvicorn examples.fastapi.sdk_frontend:app
"""

import time
from typing import Annotated

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from func_to_web import Max, Min, router_of

PREFIX = "/tools"

TITLE = "Internal tools"

STEP_SECONDS = 0.2

TEMPLATE = """\
<!doctype html>
<html>
<body>
<button id="add">add(2, 3)</button>
<button id="convert">convert(4)</button>
<button id="open">open add in a modal</button>
<pre id="log"></pre>
<script type="module">
import { call, callStream, openModal } from "__PREFIX__/static/sdk.js";

const log = document.getElementById("log");

const write = (text) => { log.textContent += `${text}\\n`; };

document.getElementById("add").addEventListener("click", async () => {
    try {
        const outputs = await call("__PREFIX__/add", {a: 2, b: 3});
        write(outputs[0].value);
    } catch (error) {
        write(`${error.status}: ${error.message}`);
    }
});

document.getElementById("convert").addEventListener("click", async () => {
    const outputs = await callStream("__PREFIX__/convert", {files: 4}, {
        onPrint: (text) => write(text.trimEnd()),
    });

    write(outputs[0].value);
});

document.getElementById("open").addEventListener("click", () => {
    openModal("__PREFIX__/add", {
        prefill: {a: 2},
        onClose: () => write("closed"),
    });
});
</script>
</body>
</html>
"""

PAGE = TEMPLATE.replace("__PREFIX__", PREFIX)


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def convert(files: Annotated[int, Min(1), Max(8)] = 5) -> str:
    """Report the progress of a slow job while it advances."""
    for index in range(1, files + 1):
        time.sleep(STEP_SECONDS)
        print(f"file {index} of {files}")

    return f"{files} file(s) converted"


SPACE = [add, convert]

app = FastAPI()

app.include_router(router_of(SPACE, title=TITLE), prefix=PREFIX)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Serve the frontend that imports sdk.js."""
    return PAGE


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
