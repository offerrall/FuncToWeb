import json
from datetime import timedelta
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import unquote_to_bytes

from pytypehintweb import STATIC
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    Response,
    StreamingResponse,
)
from starlette.routing import Route
from starlette.types import ASGIApp, Receive, Scope, Send

from func_to_web.config import checked_returns_dir, checked_uploads_dir
from func_to_web.models.function import WebFunction, build_prefill, page_of
from func_to_web.models.functions import FormAction, FunctionInput, space_of
from func_to_web.templates.index import index_of
from func_to_web.templates.theme import Theme, checked_theme
from func_to_web.web.execution import execute
from func_to_web.web.messages import without_storage_paths
from func_to_web.web.returned_files import stored_return
from func_to_web.web.stream import stream
from func_to_web.web.upload import (
    DEFAULT_TTL,
    checked_limit,
    checked_ttl,
    start_pending,
    start_returns,
    stored_file,
    uploader,
)

STATIC_CACHE: str = "public, max-age=3600"

STATIC_ROOTS: tuple[Path, ...] = (
    Path(str(files("func_to_web").joinpath("static"))).resolve(),
    STATIC.resolve(),
)

STATIC_TYPES: dict[str, str] = {
    ".js": "text/javascript",
    ".css": "text/css",
    ".svg": "image/svg+xml",
}


class DefensivePaths:
    """Reject dot segments before the router normalizes them into another URL."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # raw_path is optional in ASGI: a server that never populates it would
        # leave this middleware defending nothing, so path is the fallback.
        original = scope.get("raw_path") or scope.get("path", "").encode("utf-8")
        raw = unquote_to_bytes(original.split(b"?", 1)[0])
        if scope["type"] == "http" and b".." in raw.split(b"/"):
            response = JSONResponse({"detail": "Not Found"}, status_code=404)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def static_asset(name: str) -> Path | None:
    if not name:
        return None

    for root in STATIC_ROOTS:
        try:
            candidate = (root / name).resolve()

            if candidate.is_relative_to(root) and candidate.is_file():
                return candidate
        except (OSError, ValueError):
            continue

    return None


def _routes(
    web_function: WebFunction,
    capture_prints: bool,
    form: FormAction | None,
    theme: Theme,
) -> list[Route]:
    base = page_of(web_function, theme=theme)

    def page(request: Request) -> HTMLResponse:
        prefill = request.query_params.get("prefill")
        hidden = request.query_params.get("hidden")
        autorun = boolean_query(request.query_params.get("autorun"), "autorun")
        names = ([] if hidden is None
                 else hidden_names(json_query(hidden, "hidden")))
        raw: Any = {} if prefill is None else json_query(prefill, "prefill")

        if prefill is not None and type(raw) is not dict:
            raise HTTPException(400, "prefill must be a JSON object")

        if not raw and not names and not autorun:
            return HTMLResponse(base)

        try:
            values = (build_prefill(web_function.schema, raw,
                                    file_resolver=stored_file)
                      if raw else None)
            rendered = page_of(web_function, prefill=values, hidden=names,
                               autorun=autorun, theme=theme)
            return HTMLResponse(rendered)
        except (TypeError, ValueError, FileNotFoundError) as error:
            raise HTTPException(
                400, without_storage_paths(str(error))
            ) from error

    async def invoke(request: Request) -> JSONResponse:
        data = await json_body(request)
        envelope, status = await execute(web_function, data, form=form)
        return JSONResponse(envelope, status_code=status)

    async def invoke_stream(request: Request) -> StreamingResponse:
        data = await json_body(request)
        return stream(web_function, data, capture_prints=capture_prints,
                      form=form)

    slug = web_function.slug
    return [
        Route(f"/{slug}/", page, methods=["GET"]),
        Route(f"/{slug}/invoke", invoke, methods=["POST"]),
        Route(f"/{slug}/invoke-stream", invoke_stream, methods=["POST"]),
    ]


async def json_body(request: Request) -> dict[str, Any]:
    try:
        raw = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise HTTPException(422, "body must be valid JSON") from error

    if type(raw) is not dict:
        raise HTTPException(422, "body must be a JSON object")

    return raw


def boolean_query(value: str | None, name: str) -> bool:
    if value is None:
        return False

    normalized = value.lower()
    if normalized in {"1", "true", "on", "yes"}:
        return True
    if normalized in {"0", "false", "off", "no"}:
        return False

    raise HTTPException(422, f"{name} must be a boolean")


def json_query(value: str, name: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as error:
        raise HTTPException(400, f"{name} must be valid JSON") from error


def hidden_names(raw: Any) -> list[str]:
    if type(raw) is not list:
        raise HTTPException(400, "hidden must be a JSON array")

    for item in raw:
        if type(item) is not str:
            raise HTTPException(400, "hidden must contain only strings")

    return raw


def captures_prints(web_function: WebFunction, space: bool | None) -> bool:
    if web_function.capture_prints is not None:
        return web_function.capture_prints

    return True if space is None else space


def app_of(
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
) -> Starlette:
    """Build a mountable Starlette application for a space of functions."""
    limit = checked_limit(max_upload_bytes)
    ttl = checked_ttl(pending_ttl, "pending_ttl")
    returns = checked_ttl(returns_ttl, "returns_ttl")
    uploads_root = checked_uploads_dir(uploads_dir)
    returns_root = checked_returns_dir(returns_dir)
    chosen = checked_theme(theme)
    web_functions = space_of(fns, title)
    routes: list[Route] = []

    for web_function in web_functions.functions:
        routes.extend(_routes(
            web_function,
            captures_prints(web_function, capture_prints),
            web_functions.forms.get(web_function.slug),
            chosen,
        ))

    if web_functions.uploads:
        routes.append(Route("/upload", uploader(limit), methods=["POST"]))
        start_pending(uploads_root, ttl)

    if web_functions.returns:
        def returned(request: Request) -> FileResponse:
            try:
                path, filename = stored_return(request.path_params["reference"])
            except (ValueError, FileNotFoundError) as error:
                raise HTTPException(404) from error

            return FileResponse(path, filename=filename,
                                media_type="application/octet-stream")

        routes.append(Route("/returns/{reference}", returned,
                            methods=["GET"]))
        start_returns(returns_root, returns)

    def documentation(request: Request) -> PlainTextResponse:
        return PlainTextResponse(web_functions.document)

    def static(request: Request) -> Response:
        path = static_asset(request.path_params["name"])

        if path is None:
            raise HTTPException(404)

        response = FileResponse(
            path,
            stat_result=path.stat(),
            media_type=STATIC_TYPES.get(path.suffix.lower()),
            headers={"Cache-Control": STATIC_CACHE},
        )
        etag = response.headers["etag"]

        if request.headers.get("if-none-match") == etag:
            return Response(
                status_code=304,
                headers={"ETag": etag, "Cache-Control": STATIC_CACHE},
            )

        return response

    def index(request: Request) -> HTMLResponse:
        return HTMLResponse(index_of(web_functions, ".", chosen))

    routes.extend([
        Route("/doc", documentation, methods=["GET"]),
        Route("/static/{name:path}", static, methods=["GET"]),
        Route("/", index, methods=["GET"]),
    ])

    async def http_error(request: Request, error: Exception) -> JSONResponse:
        assert isinstance(error, HTTPException)
        return JSONResponse({"detail": error.detail},
                            status_code=error.status_code,
                            headers=error.headers)

    app = Starlette(
        routes=routes,
        exception_handlers={HTTPException: http_error},
    )
    app.add_middleware(DefensivePaths)
    setattr(app, "title", web_functions.title)
    return app
