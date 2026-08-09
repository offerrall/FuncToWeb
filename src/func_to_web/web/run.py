from datetime import timedelta
from pathlib import Path
from typing import Any

from func_to_web.config import NAME, __version__
from func_to_web.models.functions import FunctionInput, space_of
from func_to_web.templates.theme import Theme
from func_to_web.web import returned_files, upload
from func_to_web.web.router import app_of
from func_to_web.web.upload import DEFAULT_TTL


def run(
    fns: FunctionInput,
    *,
    title: str | None = None,
    capture_prints: bool | None = None,
    max_upload_bytes: int | None = None,
    pending_ttl: int | timedelta | None = DEFAULT_TTL,
    returns_ttl: int | timedelta | None = DEFAULT_TTL,
    uploads_dir: str | Path | None = None,
    returns_dir: str | Path | None = None,
    theme: Theme = "system",
    host: str = "127.0.0.1",
    port: int = 8000,
    uvicorn_kwargs: dict[str, Any] | None = None,
) -> None:
    """Serve a space of functions as a standalone ASGI application.

    Takes the same space and options as app_of(). host and port configure
    Uvicorn. A key run() already owns ("host", "port", "app") raises
    TypeError. Blocks until the server stops.
    """
    server_options = {} if uvicorn_kwargs is None else dict(uvicorn_kwargs)

    if "host" in server_options:
        raise TypeError(
            "uvicorn_kwargs cannot contain 'host'; use the host argument"
        )

    if "port" in server_options:
        raise TypeError(
            "uvicorn_kwargs cannot contain 'port'; use the port argument"
        )

    if "app" in server_options:
        raise TypeError(
            "uvicorn_kwargs cannot contain 'app'; run() builds it internally"
        )

    space = space_of(fns, title)
    app = app_of(
        space,
        capture_prints=capture_prints,
        max_upload_bytes=max_upload_bytes,
        pending_ttl=pending_ttl,
        returns_ttl=returns_ttl,
        uploads_dir=uploads_dir,
        returns_dir=returns_dir,
        theme=theme,
    )

    import uvicorn

    print(
        f"{NAME} {__version__}\n"
        f"UPLOADS DIR: {upload.UPLOADS_DIR}\n"
        f"RETURNS DIR: {returned_files.RETURNS_DIR}",
        flush=True,
    )

    uvicorn.run(
        app,
        host=host,
        port=port,
        **server_options,
    )
