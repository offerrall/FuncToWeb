import io
import base64
from .types import FileResponse, ActionTable
from .core.return_file_handler import save_returned_file
from .core.table import try_process_table
from .core.utils import slugify


def process_error(exc: Exception) -> dict:
    """Return an error result from an exception."""
    return {"type": "error", "data": str(exc)}


def process_str(s: str) -> dict:
    """Return a text result."""
    return {"type": "text", "data": s}


def process_pil_image(image) -> dict:
    """Convert a PIL Image to a base64 PNG data URI."""
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    image.close()
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    return {"type": "image", "data": f"data:image/png;base64,{b64}"}


def process_matplotlib_figure(figure) -> dict:
    """Convert a matplotlib Figure to a base64 PNG data URI."""
    import matplotlib.pyplot as plt  # avoid hard dependency at import time

    buf = io.BytesIO()
    figure.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(figure)
    return {"type": "image", "data": f"data:image/png;base64,{b64}"}


def process_file_response(file_response: FileResponse) -> dict:
    """Save a FileResponse and return a download descriptor."""
    file_id, _ = save_returned_file(file_response)
    return {
        "type": "download",
        "file_id": file_id,
        "filename": file_response.filename,
    }


def process_file_response_list(items: list[FileResponse]) -> dict:
    """Save multiple FileResponse objects and return a batch download descriptor."""
    files = []
    for f in items:
        file_id, _ = save_returned_file(f)
        files.append({"file_id": file_id, "filename": f.filename})
    return {"type": "downloads", "files": files}


def process_action_table(t: ActionTable) -> dict:
    """Serialize an ActionTable into a navigable table descriptor."""
    slug = slugify(t.action.__name__.replace("_", " "))
    return {
        "type": "action_table",
        "headers": t.headers,
        "rows": t.rows,
        "action": f"/{slug}",
    }


def _is_pil_image(obj) -> bool:
    """Check if object is a PIL Image (safe if PIL not installed)."""
    try:
        from PIL import Image
        return isinstance(obj, Image.Image)
    except ImportError:
        return False


def _is_matplotlib_figure(obj) -> bool:
    """Check if object is a matplotlib Figure (safe if matplotlib not installed)."""
    try:
        from matplotlib.figure import Figure
        return isinstance(obj, Figure)
    except ImportError:
        return False


def _process_single(result) -> dict:
    """Serialize a single return value.

    Order matters:
    - None → "Done"
    - list/tuple → recursive
    - str → text
    - ActionTable → action_table
    - FileResponse → download
    - PIL → image
    - matplotlib → image
    - table-like → table
    - fallback → str()
    """
    if result is None:
        return process_str("Done")

    if isinstance(result, (tuple, list)):
        return process_result(result)

    if isinstance(result, str):
        return process_str(result)

    if isinstance(result, ActionTable):
        return process_action_table(result)

    if isinstance(result, FileResponse):
        return process_file_response(result)

    if _is_pil_image(result):
        return process_pil_image(result)

    if _is_matplotlib_figure(result):
        return process_matplotlib_figure(result)

    # Try structured table formats (list[dict], dataclasses, etc.)
    table = try_process_table(result)
    if table is not None:
        return table

    return process_str(str(result))


def process_result(result) -> dict:
    """Top-level dispatcher for function return values.

    Handles sequences first, then falls back to single-value processing.
    """
    if isinstance(result, (tuple, list)):
        if len(result) == 0:
            return process_str("Done")

        if all(isinstance(item, FileResponse) for item in result):
            return process_file_response_list(list(result))

        table = try_process_table(result)
        if table is not None:
            return table

        items = [_process_single(item) for item in result if item is not None]

        if len(items) == 1:
            return items[0]

        if len(items) > 1:
            return {"type": "multiple", "data": items}

    return _process_single(result)