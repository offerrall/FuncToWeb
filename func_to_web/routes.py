import re

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse as FastAPIFileResponse, JSONResponse
from fastapi.responses import PlainTextResponse

from .builder import render_index
from .models import FunctionMetadata, NormalizedInput
from .core.docs import build_doc
from .core.normalization import get_all_functions
from .core.return_file_handler import get_returned_file
from .route_handlers import create_handlers


UUID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


def register_function_routes(
    app: FastAPI,
    meta: FunctionMetadata,
    app_input: NormalizedInput,
    url: str
) -> None:
    """Register routes for a single function."""
    page_handler, submit_handler = create_handlers(meta, app_input, base_url=url)

    app.get(url, response_class=HTMLResponse)(page_handler)
    app.post(f"{url}/submit")(submit_handler)


def register_navigation_routes(
    app: FastAPI,
    nav_items: list,
    app_input: NormalizedInput
) -> None:
    """Recursively register routes for all navigation items."""
    # Resolve all functions once, then match them by slug.
    all_functions = get_all_functions(app_input.items)

    for item in nav_items:
        if item["type"] == "function":
            meta = next((m for m in all_functions if m.slug == item["slug"]), None)
            if meta:
                register_function_routes(app, meta, app_input, item["url"])
        else:
            register_navigation_routes(app, item["children"], app_input)


def setup_multi_items(app: FastAPI, app_input: NormalizedInput) -> None:

    visible = [item for item in app_input.navigation_data if item["type"] == "function" and not item.get("hidden")]

    @app.get("/", response_class=HTMLResponse)
    async def index():
        if len(visible) == 1:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=visible[0]["url"])
        return render_index(app_input)

    register_navigation_routes(app, app_input.navigation_data, app_input)


def setup_single_function(app: FastAPI, app_input: NormalizedInput) -> None:
    """Set up routes for single-function mode."""
    meta = app_input.single_function

    page_handler, submit_handler = create_handlers(meta, app_input, base_url="")

    app.get("/", response_class=HTMLResponse)(page_handler)
    app.post("/submit")(submit_handler)


def setup_download_route(app: FastAPI) -> None:
    """Register the file download route."""

    @app.get("/download/{file_id}")
    async def download_file(file_id: str):
        # Reject invalid IDs before touching the file store.
        if not UUID_PATTERN.match(file_id):
            return JSONResponse({"error": "Invalid file ID"}, status_code=400)

        file_info = get_returned_file(file_id)
        if not file_info:
            return JSONResponse({"error": "File not found or expired"}, status_code=404)

        return FastAPIFileResponse(
            path=file_info["path"],
            filename=file_info["filename"],
            media_type="application/octet-stream",
        )

def setup_doc_route(app: FastAPI, app_input: NormalizedInput) -> None:
    @app.get("/doc", response_class=PlainTextResponse)
    async def doc():
        return build_doc(app_input)