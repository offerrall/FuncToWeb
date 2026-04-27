from typing import Any
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from .constants import STATIC_DIR, UVICORN_DEFAULTS


def create_fastapi_app(
    root_path: str = "",
    fastapi_config: dict[str, Any] | None = None,
    front_dir: str | Path | None = None,
    assets_dir: str | Path | None = None,
) -> FastAPI:
    """Create and configure the FastAPI app (including /static)."""
    base_config = {"root_path": root_path}

    if fastapi_config:
        clean_config = {k: v for k, v in fastapi_config.items() if k != "root_path"}
        base_config.update(clean_config)

    app = FastAPI(**base_config)

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    if front_dir is not None:
        app.mount("/front", StaticFiles(directory=Path(front_dir), html=True), name="front")

    if assets_dir is not None:
        app.mount("/assets", StaticFiles(directory=Path(assets_dir)), name="assets")

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

    clean_kwargs = {k: v for k, v in uvicorn_kwargs.items() if k != "root_path"}
    config.update(clean_kwargs)

    uvicorn_config = uvicorn.Config(app, **config)
    server = uvicorn.Server(uvicorn_config)

    server.run()