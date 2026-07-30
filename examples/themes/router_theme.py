"""The theme belongs to the space: two themes are two routers."""

import uvicorn
from fastapi import FastAPI

from func_to_web import router_of

HOST = "127.0.0.1"
PORT = 8000


def word_count(text: str = "Two themes, one function") -> str:
    """Count the words of a sentence."""
    return f"{len(text.split())} words"


def build_app() -> FastAPI:
    """Mount the same function twice, one router per forced theme.

    The theme belongs to the space and not to the function, so two themes
    need two routers. A WebFunction compiles its page once and without
    knowing where it will be mounted, which is why it carries no theme.
    """
    app = FastAPI()

    app.include_router(
        router_of(word_count, title="Light space", theme="light"),
        prefix="/light",
    )
    app.include_router(
        router_of(word_count, title="Dark space", theme="dark"),
        prefix="/dark",
    )

    return app


if __name__ == "__main__":
    print(f"Light: http://{HOST}:{PORT}/light/word_count/")
    print(f"Dark:  http://{HOST}:{PORT}/dark/word_count/")

    uvicorn.run(build_app(), host=HOST, port=PORT)
