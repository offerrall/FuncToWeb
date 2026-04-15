from typing import Any
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from .constants import STATIC_DIR, UVICORN_DEFAULTS


def create_fastapi_app(
    root_path: str = "",
    fastapi_config: dict[str, Any] | None = None
) -> FastAPI:
    """Create and configure the FastAPI app (including /static)."""
    base_config = {"root_path": root_path}

    if fastapi_config:
        # Prevent overriding root_path twice
        clean_config = {k: v for k, v in fastapi_config.items() if k != "root_path"}
        base_config.update(clean_config)

    app = FastAPI(**base_config)

    # Serve static assets (CSS, JS, images)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    return app


def start_server(
    app: FastAPI,
    host: str,
    port: int,
    uvicorn_kwargs: dict[str, Any]
) -> None:
    """Start the Uvicorn server with merged default + user config."""
    config = {
        "host": host,
        "port": port,
        **UVICORN_DEFAULTS,
    }

    # Avoid passing root_path twice (handled by FastAPI)
    clean_kwargs = {k: v for k, v in uvicorn_kwargs.items() if k != "root_path"}
    config.update(clean_kwargs)

    uvicorn_config = uvicorn.Config(app, **config)
    server = uvicorn.Server(uvicorn_config)

    server.run()