import json

from .normalization import get_all_functions
from ..route_handlers import _analyze


_INTRO = """=== FuncToWeb API ===

Each Python function is exposed as a POST endpoint. UI and API share the
same URL — this document only covers the API.


=== Request format ===

  POST <base_url>/<slug>/submit
  Content-Type: multipart/form-data

  - Non-file params:  one field "values" with a JSON object.
  - File params:      one multipart field per param (name = param name).
                      Repeat the field for list[File].

Example with mixed params:

  curl -X POST <base_url>/create-product/submit \\
    -F 'values={"name": "Widget", "price": 9.99}' \\
    -F 'photos=@./photo1.jpg' \\
    -F 'photos=@./photo2.jpg'


=== Parameter schema ===

Each endpoint declares its parameters as a JSON object. Per-field keys:

  param_type     "str" | "int" | "float" | "bool" | "date" | "time"
  default        value used when the field is omitted from "values"
  constraints    { ge, le, gt, lt, min_length, max_length, pattern }
  choices        { options: [...], dynamic?: true }
                   - closed set when dynamic is absent
                   - dynamic=true means the snapshot may be stale; the server
                     accepts other values and the function validates them
  list           present → param accepts an array
  optional       present → param accepts null (omit it from "values")
  special_widget "File" → send as multipart, not inside "values"
  upload_info    { field_name, multiple } for File params


=== Response format ===

HTTP 200 → Server-Sent Events stream:

  event: start
  data: {}

  event: print           (zero or more, only if the function uses print())
  data: ["line", ...]

  event: result
  data: { ...see shapes below... }

The "result" event always has "success" (bool). On success, "type" tells
you which shape to expect:

  text          { success, type: "text",   data: "..." }
  image         { success, type: "image",  data: "data:image/png;base64,..." }
  table         { success, type: "table",  headers: [...], rows: [[...]] }
  action_table  { success, type: "action_table", headers, rows,
                  action: "/<slug>" }   ← treat as table from the API
  download      { success, type: "download",  file_id, filename }
                  Fetch with: GET <base_url>/download/<file_id>
                  Files expire (default 1h).
  downloads     { success, type: "downloads", files: [{file_id, filename}] }
  multiple      { success, type: "multiple", data: [<shape>, <shape>, ...] }
                  Mixed return values; each item is one of the shapes above.

On failure inside the function:

  error         { success: false, type: "error", data: "<message>" }


=== Other failure modes ===

  HTTP 422   Input validation failed (no stream).
             { success: false, errors: { "<param>": "<message>", ... } }

  HTTP 400   Malformed request, e.g. invalid JSON in "values" (no stream).
             { success: false, error: "<message>" }


=== Notes ===

- Ignore "print" events if you only want the final result.
- Omit optional params from "values" to send null.
- Hidden endpoints work like visible ones; they're just not in the index.


=== Endpoints ===
"""


# Keys to strip from each param dict before serializing —
# they're cosmetic UI hints with no effect on the API call.
_DROP_KEYS = {"item_ui", "param_ui", "name"}


def build_doc(app_input) -> str:
    """Build the full API documentation as a single string."""
    if app_input.single_function:
        funcs = [app_input.single_function]
    else:
        funcs = get_all_functions(app_input.items)

    parts = [_INTRO]
    for meta in funcs:
        parts.append(_doc_for_function(meta))

    return "\n".join(parts)


def _doc_for_function(meta) -> str:
    """Build the documentation block for a single function."""
    params, _ = _analyze(meta.function)

    header = (
        f"\n--- /{meta.slug} ---\n"
        f"Name: {meta.name}\n"
    )
    if meta.hidden:
        header += "Hidden: true\n"
    if meta.description:
        header += f"Description: {meta.description}\n"

    if not params:
        return header + "Parameters: none\n"

    params_dict = {}
    for p in params:
        d = {k: v for k, v in p.to_dict().items() if k not in _DROP_KEYS}

        if d.get("special_widget") == "File":
            d["upload_info"] = {
                "field_name": p.name,
                "multiple": "list" in d,
            }

        if p.choices is not None and p.choices.options_function is not None:
            d.setdefault("choices", {})["dynamic"] = True

        params_dict[p.name] = d

    return header + "Parameters:\n" + json.dumps(params_dict, indent=2, default=str) + "\n"