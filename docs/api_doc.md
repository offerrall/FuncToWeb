# API Documentation Endpoint

Every FuncToWeb app exposes a plain-text, machine-readable description of all its endpoints at `/doc`. Any HTTP client, script, or LLM can read it and call the functions without prior knowledge of the app — no SDK, no protocol, just HTTP.

## Quick look

```bash
curl http://127.0.0.1:8000/doc
```

The response is plain text with two parts: a general intro explaining how to call any endpoint, and one block per registered function (visible and hidden) with its name, parameters as JSON, and a working `curl` example.

## What's in each function block

For every function you get:

- The slug and URL.
- Whether it's hidden from the web UI.
- Its description (from the docstring).
- Parameters as JSON: type, default, constraints, choices, list/optional flags, and `upload_info` for file fields.
- A ready-to-run `curl` example using `<base_url>` as a placeholder.

Static dropdowns are listed as a closed set; dynamic ones (`Dropdown(func)`) are flagged with `"dynamic": true` so consumers know the listed options are a snapshot.

## What's in the response section

The intro also documents the response format:

- Success responses are a Server-Sent Events stream with `start`, `print`, and `result` events.
- The `result` event carries a JSON object with `success` and `type` (`text`, `image`, `table`, `action_table`, `download`, `downloads`, `multiple`, or `error`).
- Validation errors return HTTP 422 with a JSON body listing the offending fields.

## Calling endpoints from code

Once you've read `/doc`, calling any endpoint is a regular HTTP POST:

```python
import requests, json

r = requests.post(
    "http://127.0.0.1:8000/create-tag/submit",
    data={"values": json.dumps({"name": "demo"})},
    stream=True,
)
for line in r.iter_lines(decode_unicode=True):
    if line.startswith("data:") and "result" in line:
        print(line)
```

For file uploads, send each file as a separate multipart field with the parameter name (the doc spells out the field name for you in `upload_info`).

## Why this exists

The same mechanism that powers the web UI (typed parameters, validation, file handling) doubles as a self-describing API. You write your function once and get:

- A web form for humans.
- Embeddable iframes via URL prefill (see [URL Prefill](url_prefill.md)) and embed mode (see [Embed Mode](embed.md)).
- A scriptable, agent-callable API via `/doc`.

No extra code, no extra dependencies.