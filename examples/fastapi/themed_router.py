"""Two applications over the same functions, one per theme.

The theme belongs to the space and is written into the <html> that the server
sends, so it is resolved before the first paint. A WebFunction carries no
theme of its own: two themes need two applications, one per mount point. Serve it
as a script or point uvicorn at the module:
uvicorn examples.fastapi.themed_router:app
"""

import uvicorn
from fastapi import FastAPI

from func_to_web import app_of


def word_count(text: str) -> str:
    """Count the words of a piece of text."""
    return f"{len(text.split())} word(s)"


app = FastAPI()

app.mount("/light", app_of([word_count], title="Daylight tools", theme="light"))

app.mount("/dark", app_of([word_count], title="Night tools", theme="dark"))

app.mount("/system", app_of([word_count], title="System tools"))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
