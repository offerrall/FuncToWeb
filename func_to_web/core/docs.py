import json
import re

from .normalization import get_all_functions
from ..route_handlers import _analyze


_INTRO = """=== FuncToWeb API ===

This server exposes Python functions as HTTP endpoints. Each endpoint also
has a web UI at the same URL, but you can call them directly from code.

The URL prefixes shown in the examples (such as `<base_url>`) refer to the
host where this server is reachable. Replace it with the actual address you
are using to reach this API (for example, http://127.0.0.1:8000 in local
development, or https://your-domain.com in production).


=== Making a request ===

How to call any endpoint:
- Method:       POST
- URL:          <base_url>/<function-slug>/submit
- Body:         multipart/form-data
- Non-file params: a single field named "values" containing a JSON object
- File params:  one separate multipart field per file, named after the parameter

Minimal example:

  curl -X POST <base_url>/divide/submit \\
    -F 'values={"a": 10, "b": 2}'

Example with one file:

  curl -X POST <base_url>/upload-gcode/submit \\
    -F 'values={}' \\
    -F 'file=@./model.gcode'

Example with multiple files (list parameter):

  curl -X POST <base_url>/create-product/submit \\
    -F 'values={"name": "Widget", "price": 9.99}' \\
    -F 'photos=@./photo1.jpg' \\
    -F 'photos=@./photo2.jpg'


=== Reading the parameters block ===

Each endpoint lists its parameters as a JSON object. Each entry can include:

- "param_type": Python type name ("str", "int", "float", "bool", "date", "time").
- "default": value used when the parameter is omitted from "values".
- "constraints": validation rules. Possible keys:
    - "ge", "le", "gt", "lt": numeric bounds
    - "min_length", "max_length": string or list length bounds
    - "pattern": regex the value must match
- "choices.options": valid values for the parameter (closed set).
- "choices.dynamic": when true, the listed options are a snapshot at
  doc-generation time. The server will accept other values; the function
  is responsible for validating them.
- "list": present when the parameter accepts an array of values.
- "optional.enabled": present when the parameter is optional. Omit it from
  "values" to send null.
- "special_widget": "File" means the parameter is a file upload, not a
  string. Send it as a separate multipart field, not inside "values".
- "upload_info": for file parameters, describes how to send the file:
    - "transport": always "multipart/form-data"
    - "field_name": multipart field name to use
    - "multiple": true if the field accepts more than one file
- "item_ui" and "param_ui": purely cosmetic UI hints (placeholders, labels,
  slider rendering, textarea rows). Safe to ignore for API calls.


=== Reading the response ===

Successful calls (HTTP 200) return a Server-Sent Events stream with these
events, in order:

  event: start
  data: {}

  event: print            (zero or more, only if the function uses print())
  data: ["line 1", "line 2"]

  event: result
  data: { ...see below... }

The "result" event always carries a JSON object with a "success" boolean.

When "success" is true, the object also has a "type" field describing the
shape of the result. These are all the possible shapes:

  { "success": true, "type": "text",
    "data": "..." }
      → plain text. Also used for None (data is "Done") and any non-special
        return value (cast with str()).

  { "success": true, "type": "image",
    "data": "data:image/png;base64,..." }
      → a PIL Image or matplotlib Figure, encoded as a PNG data URI.

  { "success": true, "type": "table",
    "headers": ["col1", "col2", ...],
    "rows": [["v1", "v2", ...], ...] }
      → tabular data (list[dict], list[tuple], pandas/polars DataFrame,
        numpy 2D array). All cells are strings.

  { "success": true, "type": "action_table",
    "headers": [...], "rows": [...],
    "action": "/<other-slug>" }
      → same as "table", with an extra "action" pointing to another endpoint.
        In the web UI a row click navigates to that endpoint with the row
        data as prefill. From an API client, treat it like a regular table:
        read the rows, then call "action" yourself with the values you need.

  { "success": true, "type": "download",
    "file_id": "<32-hex>", "filename": "..." }
      → a generated file. Fetch the bytes with:
            GET <base_url>/download/<file_id>
        Returned files are kept on disk for a limited time (default 1 hour),
        then deleted. Download promptly.

  { "success": true, "type": "downloads",
    "files": [{"file_id": "...", "filename": "..."}, ...] }
      → multiple generated files. Same fetch URL per file_id.

  { "success": true, "type": "multiple",
    "data": [<result object>, <result object>, ...] }
      → the function returned a tuple/list mixing several result types.
        Each item in "data" is one of the shapes above (text, image, table,
        download...). None values are filtered out.

When "success" is false:

  { "success": false, "type": "error",
    "data": "<error message>" }
      → the function raised an exception. The message is exc's str().

Other failure modes:

- HTTP 422 (no SSE stream) — input validation failed before the function
  ran. Body:
        { "success": false, "errors": { "<param>": "<message>", ... } }
  Inspect "errors" to know which fields to fix.

- HTTP 400 (no SSE stream) — malformed request (e.g. invalid JSON in
  "values"). Body:
        { "success": false, "error": "<message>" }


=== Notes ===

- The "print" events are optional. If you don't care about progress output,
  ignore them and read only the final "result" event.
- Defaults are shown when present; omit a parameter from "values" to use
  its default. For optional parameters, omitting them sends null.
- Hidden endpoints (Hidden: true) are reachable from the API exactly like
  visible ones. They are simply not listed in the web UI.

=== Endpoints ===
"""


def build_doc(app_input) -> str:
    """Build the full API documentation as a single string."""
    if app_input.single_function:
        all_funcs = [app_input.single_function]
    else:
        all_funcs = get_all_functions(app_input.items)

    parts = [_INTRO]

    for meta in all_funcs:
        parts.append(_doc_for_function(meta))

    return "\n".join(parts)


def _doc_for_function(meta) -> str:
    """Build the documentation block for a single function."""
    params, _ = _analyze(meta.function)

    params_dict = {}
    for p in params:
        d = p.to_dict()
        d.pop("name", None)

        if d.get("special_widget") == "File":
            d["upload_info"] = {
                "transport": "multipart/form-data",
                "field_name": p.name,
                "multiple": "list" in d,
            }

        if p.choices is not None and p.choices.options_function is not None:
            d.setdefault("choices", {})["dynamic"] = True

        params_dict[p.name] = d

    params_json = json.dumps(params_dict, indent=2, default=str)

    curl = _build_curl(meta.slug, params)

    return (
        f"\n--- /{meta.slug} ---\n"
        f"Name: {meta.name}\n"
        f"Hidden: {str(meta.hidden).lower()}\n"
        f"Description: {meta.description}\n\n"
        f"Parameters:\n{params_json}\n\n"
        f"Example:\n{curl}\n"
    )


def _build_curl(slug: str, params) -> str:
    """Build a minimal example curl command."""
    values = {}
    file_lines = []

    for p in params:
        d = p.to_dict()

        if d.get("special_widget") == "File":
            ext = _guess_extension(d.get("constraints", {}).get("pattern", ""))
            file_lines.append(f"  -F '{p.name}=@./file.{ext}'")
        else:
            values[p.name] = _example_value(d)

    lines = [f"curl -X POST <base_url>/{slug}/submit"]
    lines.append(f"  -F 'values={json.dumps(values)}'")
    lines.extend(file_lines)

    return " \\\n".join(lines)


def _example_value(d):
    """Return a reasonable example value for a parameter."""
    ptype = d.get("param_type", "str")

    choices = d.get("choices")
    if choices and choices.get("options"):
        val = choices["options"][0]
        return [val] if "list" in d else val

    constraints = d.get("constraints", {})

    if ptype == "int":
        val = constraints.get("ge", constraints.get("gt", 0) + 1 if "gt" in constraints else 1)
    elif ptype == "float":
        val = constraints.get("ge", constraints.get("gt", 0) + 0.01 if "gt" in constraints else 1.0)
    elif ptype == "bool":
        val = True
    elif ptype == "str":
        min_len = constraints.get("min_length", 1)
        val = "a" * max(min_len, 1) if min_len > 7 else "example"
    else:
        val = "example"

    return [val] if "list" in d else val


def _guess_extension(pattern: str) -> str:
    """Extract the first valid extension from a file pattern."""
    m = re.search(r"\(([\w|]+)\)", pattern)
    if m:
        return m.group(1).split("|")[0]
    return "bin"