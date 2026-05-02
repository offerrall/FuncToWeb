# Prefill URL Contract

This document describes how a client library (e.g. a Python backend, a router redirect, or any code that **generates** URLs pointing at a `<pti-form>`) must construct query strings so that prefill works correctly.

PyTypeInputWeb reads `window.location.search` on mount and applies each query parameter to the field with the same name. The library does **not** apply heuristics to "clean" the values — what you put in the URL is what gets written into the field.

---

## The golden rule

> **To represent "no value" (Python `None`, JS `null`, missing, undefined), OMIT the parameter from the URL entirely.**

Do **not** serialize null-like values as the strings `"None"`, `"null"`, `"undefined"`, or any other placeholder. The library will treat those as real string values and:

- For optional fields → activate the toggle with that literal string.
- For list fields → fail to JSON-parse and leave the list at its defaults (toggle still gets activated).
- For string fields → write the literal text into the input.

This is the single most common source of prefill bugs. Always filter `None` before encoding.

---

## Per-type encoding

| Field type | Expected URL value | Example |
|---|---|---|
| `str` | the string, URL-encoded | `?name=Alice` |
| `int` | decimal integer as string | `?age=30` |
| `float` | decimal number as string | `?ratio=1.5` |
| `bool` | `true` or `false` | `?active=true` |
| `date` | ISO `YYYY-MM-DD` | `?birthday=2026-05-02` |
| `time` | `HH:MM` or `HH:MM:SS` | `?start=09:30` |
| `color` | hex with `#` | `?color=%23ff0000` |
| dropdown / choices | the choice value as string | `?role=admin` |
| `list[X]` | **JSON-encoded array** | `?tags=%5B%22a%22%2C%22b%22%5D` |
| `Optional[X]` (None) | **omit the parameter** | — |
| `Optional[X]` (value) | encode as `X` (toggle auto-activates) | `?nickname=al` |
| `File` / file widgets | **not supported** for prefill | — |

### Notes

- **Lists must be JSON**, not Python `repr()`. `['a', 'b']` (single quotes) is not valid JSON; use `json.dumps(["a", "b"])`.
- **Datetimes**: PyTypeInputWeb has no native datetime widget. If your function takes a `datetime`, it is split into `date` + `time` widgets and you must serialize each part separately. Don't put `2026-05-02T10:06:47.457617+00:00` in a single param.
- **Files cannot be prefilled** — browsers don't allow setting `<input type="file">` values from JS for security reasons. Skip file params when building prefill URLs.

---

## Reference Python helper

```python
import json
from datetime import date, time, datetime
from urllib.parse import urlencode


def encode_prefill(values: dict) -> str:
    """Encode a dict of Python values into a query string for <pti-form> prefill.

    - None values are dropped (the form treats absent params as "no value").
    - list/tuple/dict values are JSON-encoded.
    - date/time use ISO format.
    - Files are skipped (cannot be prefilled).
    """
    encoded: dict[str, str] = {}
    for key, value in values.items():
        if value is None:
            continue
        if isinstance(value, bool):
            encoded[key] = "true" if value else "false"
        elif isinstance(value, (int, float, str)):
            encoded[key] = str(value)
        elif isinstance(value, (date, time)):
            encoded[key] = value.isoformat()
        elif isinstance(value, datetime):
            # split into separate date/time params if your form has both
            continue
        elif isinstance(value, (list, tuple, dict)):
            encoded[key] = json.dumps(value)
        # skip everything else (files, custom objects, etc.)
    return urlencode(encoded)


# Usage
url = f"/edit-user?{encode_prefill(user.dict())}"
```

---

## Anti-patterns

### Naive interpolation

```python
# BAD — Python's str(None) == "None", which the form treats as the literal string
url = f"/edit-user?id={user.id}&tags={user.tags}&nickname={user.nickname}"
```

If `user.tags is None`, this produces `?tags=None`. The form will activate the optional toggle and try to JSON-parse the string `"None"`, which fails silently. The user sees an "active" but empty list field with no explanation.

### Passing `repr()` of a list

```python
# BAD — repr uses single quotes, which are not valid JSON
url = f"/edit-form?tags={user.tags!r}"  # ?tags=['a', 'b']
```

`JSON.parse("['a', 'b']")` throws. Use `json.dumps(user.tags)` instead.

### Sending a single datetime

```python
# BAD — no datetime widget exists; the param is dropped
url = f"/edit-event?starts_at={event.starts_at.isoformat()}"
```

Split into the names your form actually exposes (e.g. `starts_at_date` + `starts_at_time`).

---

## Why the library does not "fix" this for you

It would be tempting for PyTypeInputWeb to interpret `"None"`, `"null"`, or empty strings as missing values. It deliberately does not, because:

1. URLs are strings; the only correct way to express "absent" is to omit the parameter. Adding magic placeholders creates an implicit, undocumented convention.
2. A field of type `str` could legitimately have the value `"None"` (a username, a tag, etc.). Filtering it out would silently break that use case.
3. Pushing the responsibility to the URL-generation side is a one-line fix (`if v is not None`) and keeps the form's behavior predictable.

Generate URLs correctly on the client side and prefill will work for every field type.
