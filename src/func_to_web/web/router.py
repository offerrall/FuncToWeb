import json
from datetime import timedelta
from importlib.resources import files
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    Response,
    StreamingResponse,
)

from pytypehintweb import STATIC

from func_to_web.config import checked_returns_dir, checked_uploads_dir
from func_to_web.models.function import WebFunction, build_prefill, page_of
from func_to_web.models.functions import FormAction, FunctionInput, space_of
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


def _register(
    router: APIRouter,
    web_function: WebFunction,
    capture_prints: bool,
    form: FormAction | None,
    theme: Theme,
) -> None:
    base = page_of(web_function, theme=theme)

    @router.get(f"/{web_function.slug}/", response_class=HTMLResponse)
    def page(
        prefill: str | None = Query(default=None),
        hidden: str | None = Query(default=None),
        autorun: bool = Query(default=False),
    ) -> str:
        names = ([] if hidden is None
                 else hidden_names(json_query(hidden, "hidden")))

        raw: Any = {} if prefill is None else json_query(prefill, "prefill")

        if prefill is not None and type(raw) is not dict:
            raise HTTPException(400, "prefill must be a JSON object")

        if not raw and not names and not autorun:
            return base

        try:
            values = (build_prefill(web_function.schema, raw,
                                    file_resolver=stored_file)
                      if raw else None)
            return page_of(web_function, prefill=values, hidden=names,
                           autorun=autorun, theme=theme)
        except (TypeError, ValueError, FileNotFoundError) as error:
            raise HTTPException(
                400, without_storage_paths(str(error))
            ) from error

    @router.post(f"/{web_function.slug}/invoke")
    async def invoke(data: dict[str, Any]) -> JSONResponse:
        envelope, status = await execute(web_function, data, form=form)

        return JSONResponse(envelope, status_code=status)

    @router.post(f"/{web_function.slug}/invoke-stream")
    async def invoke_stream(data: dict[str, Any]) -> StreamingResponse:
        return stream(web_function, data, capture_prints=capture_prints,
                      form=form)


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


def router_of(
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
) -> APIRouter:
    """Build the APIRouter that serves a space of functions.

    fns is a callable, a WebFunction, an iterable of either, or an already
    prepared WebFunctions —which carries its own title, so title must be None
    then. Every route is relative, so any include_router() prefix works.
    Raises TypeError or ValueError for an invalid space, theme, limit, TTL or
    storage directory.
    """
    limit = checked_limit(max_upload_bytes)
    ttl = checked_ttl(pending_ttl, "pending_ttl")
    returns = checked_ttl(returns_ttl, "returns_ttl")
    uploads_root = checked_uploads_dir(uploads_dir)
    returns_root = checked_returns_dir(returns_dir)
    chosen = checked_theme(theme)
    web_functions = space_of(fns, title)

    router = APIRouter()

    for web_function in web_functions.functions:
        _register(router, web_function,
                  captures_prints(web_function, capture_prints),
                  web_functions.forms.get(web_function.slug),
                  chosen)

    if web_functions.uploads:
        router.add_api_route("/upload", uploader(limit), methods=["POST"])
        start_pending(uploads_root, ttl)

    if web_functions.returns:
        @router.get("/returns/{reference}")
        def returned(reference: str) -> FileResponse:
            try:
                path, filename = stored_return(reference)
            except (ValueError, FileNotFoundError) as error:
                raise HTTPException(404) from error

            return FileResponse(path, filename=filename,
                                media_type="application/octet-stream")

        start_returns(returns_root, returns)

    @router.get("/doc", response_class=PlainTextResponse)
    def documentation() -> str:
        return web_functions.document

    @router.get("/static/{name:path}")
    def static(name: str, request: Request) -> Response:
        path = static_asset(name)

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

    return router
