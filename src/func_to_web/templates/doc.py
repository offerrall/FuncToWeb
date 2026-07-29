import json
from collections.abc import Iterable

from func_to_web.models.function import WebFunction

HEADER: str = """\
=== __TITLE__ ===

Every path is relative to the prefix this router is mounted on; replace
<base_url> with it.

Functions:
__FUNCTIONS__

=== Calling ===

POST <base_url>/<slug>/invoke
Content-Type: application/json

Body: a JSON object with one key per parameter, shaped as that function's Plan.
Dates and times are ISO text, an enum is its member name, a dataclass is a
nested object.

200  {"result": {"type": "text", "value": "..."}}
422  {"error": "<ExceptionType>: <message>"}  the body breaks the contract
500  {"error": "<ExceptionType>: <message>"}  the function or return failed

The answer carries "result" or "error", never both. A body that is not a JSON
object gets FastAPI's own 422 with {"detail": [...]}.

"result" holds one output, or a list of outputs in return order:

{"type": "text", "value": "..."}
{"type": "image", "value": "data:image/png;base64,..."}
{"type": "table", "headers": ["..."], "rows": [["..."]]}
{"type": "download", "value": "<reference>", "filename": "report.pdf"}
{"type": "form", "href": "../<slug>/?prefill=..."}
"""

UPLOAD: str = """\
Files: a file parameter travels as a reference string. Send the bytes first.

POST <base_url>/upload
Content-Type: application/octet-stream
X-File-Reference: <reference>

Answers {"uploaded": true}, or 413 over the space's size cap, or 409 if the
reference already exists.

An unused upload eventually expires. A reference becomes permanent the first
time an execution uses it.
"""

RETURNS: str = """\
A download output is fetched at GET <base_url>/returns/<reference>.
A download link is for fetching, not for keeping.
"""

FOOTER: str = """\
GET <base_url>/<slug>/ opens the browser form.
POST <base_url>/<slug>/invoke-stream is the same call as SSE for progress; its
final event carries the same envelope.

=== Plans ==="""


def _listing(functions: tuple[WebFunction, ...]) -> str:
    width = max((len(f.slug) for f in functions), default=0)
    lines = []

    for web_function in functions:
        slug = f"/{web_function.slug}".ljust(width + 1)
        description = (web_function.description or "").split("\n", 1)[0]
        lines.append(f"  {slug}  {description}".rstrip())

    return "\n".join(lines)


def _block(web_function: WebFunction) -> str:
    plan = json.dumps(web_function.plan, indent=2, ensure_ascii=False)

    return f"--- /{web_function.slug} ---\n\n{plan}"


def doc_of(
    functions: Iterable[WebFunction],
    *,
    title: str,
    uploads: bool,
    returns: bool,
) -> str:
    prepared = tuple(functions)
    header = HEADER.replace("__TITLE__", title)
    header = header.replace("__FUNCTIONS__", _listing(prepared))

    sections = [header.rstrip("\n")]

    if uploads:
        sections.append(UPLOAD.rstrip("\n"))

    if returns:
        sections.append(RETURNS.rstrip("\n"))

    sections.append(FOOTER)
    sections.extend(_block(web_function) for web_function in prepared)

    return "\n\n".join(sections) + "\n"
