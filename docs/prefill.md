# Prefill and OpenForm

A form can open with values already filled in, some fields hidden, or running
by itself. These options belong to one opening of the page; the function does
not change.

```text
GET /edit_user/?prefill={"name": "Ana", "age": 32}&hidden=["age"]
```

| Option | What it does |
| --- | --- |
| `prefill` | a JSON object with initial values, by parameter name |
| `hidden` | a JSON list of fields not to show; `"config.token"` and `"items.*.token"` reach nested fields |
| `autorun` | submits the form once it is ready, if nothing is missing |
| `hide_title`, `hide_description` | hide the function's heading and description |
| `hide_submit` | hides the Submit button |

The flags take `1`, `true`, `on` or `yes` (and `0`, `false`, `off`, `no`);
anything else is a `422`.

The prefill uses the same JSON as `/invoke` (dates as ISO text, an enum by its
name, a file by its reference) and it can leave out parameters, which keep
their defaults. It is validated against the signature before the page is
served, so a wrong value is a `400`, never a half-filled form:

```text
prefill={"age": "two"}   → 400 age: expected int, got str
prefill={"nope": 1}      → 400 unknown prefill field: 'nope'
```

`autorun` is for a page opened to see a result, such as a report: the page
presses its own button once. With `hide_submit` too, it shows only the result.

**`hidden` hides, it does not lock.** A hidden field still travels in the
request, and anyone can call `/invoke` with another value. The prefill travels
in the URL, so it ends up in the browser history and the server logs: it is not
a place for secrets.

## OpenForm

A function can return the values another function opens with. Mark the return
with `OpenForm` and the target function:

```python
from dataclasses import dataclass
from typing import Annotated

from func_to_web import OpenForm, run


@dataclass
class Product:
    product_id: int
    name: str
    stock: int


def edit_product(product_id: int, name: str, stock: int) -> str:
    return "Product updated"


def select_product(
    product_id: int,
) -> Annotated[Product, OpenForm(edit_product, hidden=("product_id",))]:
    return Product(product_id, "Tuna", 12)


run([select_product, edit_product])
```

Running `select_product` takes the browser to `edit_product`, with its fields
filled in and `product_id` hidden.

- Return a dataclass or a dict; it may cover only some of the parameters.
- The target must be defined first, and registered in the same space; it is
  checked when the application is built.
- `OpenForm` marks the whole return, and does not mix with other outputs.
- A file the function received can be passed on: the target opens with it
  already in place, without uploading it again.

![resize_image opened from choose_image, with its size already filled in](images/resizeimage.png)

## From Python: `page_of()`

`page_of()` builds the HTML of one opening, for a host that serves pages of its
own:

```python
page_of(
    web_function: WebFunction,
    *,
    prefill: Mapping[str, Any] | None = None,
    hidden: Iterable[str] | None = None,
    autorun: bool = False,
    hide_title: bool = False,
    hide_description: bool = False,
    hide_submit: bool = False,
    theme: Theme = "system",
) -> str
```

```python
from func_to_web import WebFunction, page_of

html = page_of(WebFunction(edit_user), prefill={"name": "Ana", "age": 32})
```

Here the prefill holds real Python values (`date`, enum members, dataclasses).
The page loads its assets from `../static/`, so it needs a space mounted beside
it.

<details>
<summary>How it works inside</summary>

A URL prefill goes through `json.loads()`, then `decode()` (which also resolves
file references), then a temporary `Signature` with only the parameters present,
whose `build()` produces exact Python values. Those go to `page_of()`, which is
where the Python entry point starts. The prefill becomes temporary defaults, so
its errors from Python carry the `default:` prefix; the function's own schema,
plan and HTML are never modified.

An `OpenForm` target is resolved by identity, not by slug: a matching slug
would not prove it is the same function. Its result reaches the browser as a
relative URL with the usual query string, so nothing is stored on the server.

</details>
