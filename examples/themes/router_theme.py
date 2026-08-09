"""The theme belongs to the space: two themes are two applications."""

import uvicorn
from fastapi import FastAPI

from func_to_web import app_of

HOST = "127.0.0.1"
PORT = 8000


def word_count(text: str = "Two themes, one function") -> str:
    """Count the words of a sentence."""
    return f"{len(text.split())} words"


def build_app() -> FastAPI:
    """Mount the same function twice, one application per forced theme.

    The theme belongs to the space and not to the function, so two themes
    need two applications. A WebFunction compiles its page once and without
    knowing where it will be mounted, which is why it carries no theme.
    """
    app = FastAPI()

    app.mount("/light", app_of(word_count, title="Light space", theme="light"))
    app.mount("/dark", app_of(word_count, title="Dark space", theme="dark"))

    return app


if __name__ == "__main__":
    print(f"Light: http://{HOST}:{PORT}/light/word_count/")
    print(f"Dark:  http://{HOST}:{PORT}/dark/word_count/")

    uvicorn.run(build_app(), host=HOST, port=PORT)
