# `OpenForm`

A function can return the data that **another** function in the same space
opens with: that data becomes its [prefill](prefill.md).

```text
OpenForm = "what I return is the prefill of that other function"
```

It is metadata on the return annotation, like [`Download`](outputs.md#downloads).
The function still returns plain Python — a dataclass or a mapping — not URLs
or navigation objects.

```python
from dataclasses import dataclass
from typing import Annotated

from func_to_web import OpenForm, run


@dataclass
class Product:
    product_id: int
    name: str
    stock: int


def edit_product(
    product_id: int,
    name: str,
    stock: int,
) -> str:
    database.update(product_id, name=name, stock=stock)
    return "Product updated"


def select_product(
    product_id: int,
) -> Annotated[
    Product,
    OpenForm(edit_product, hidden=("product_id",)),
]:
    return database.product(product_id)


run([select_product, edit_product])
```

Running `select_product` leaves the browser on the `edit_product` page, with its
three fields prefilled and `product_id` hidden.

The target function must be defined **first**: `OpenForm(edit_product)` is
evaluated when `select_product` is defined, like any other object inside
`Annotated`. The order in `run()` does not matter.

## The API

```python
@dataclass(frozen=True)
class OpenForm:
    target: Callable[..., Any] | WebFunction
    hidden: tuple[str, ...] = ()
```

`target` is the target function, or an already prepared
[`WebFunction`](web-function.md), which is useful when the target carries its
own slug. **A slug string is not accepted**: the target is the object, not its
name.

```python
edit = WebFunction(edit_product, slug="edit")

OpenForm(edit_product)
OpenForm(edit_product, hidden=("product_id",))
OpenForm(edit)
```

`hidden` is a tuple of `str` with the usual semantics: it hides the field on the
target form, without fixing or protecting it. A list, a bare string, or an
element that is not a `str` raises a `TypeError` when the metadata is built.

## The target must be registered

`OpenForm` mounts nothing, and the target is resolved when the space is built,
not the first time the function runs.

With a **callable**, the target is the registered entry whose `fn` is that same
object. If there is no such entry, or more than one, it is an error:

```python
router_of([select_product])
# ReturnContractError: OpenForm target is not registered in this space

router_of([
    WebFunction(edit_product, slug="edit-a"),
    WebFunction(edit_product, slug="edit-b"),
    select_product,
])
# ReturnContractError: OpenForm target matches more than one registered function
```

With a **`WebFunction`**, the target is that instance, and that is the instance
you must register. Here the `OpenForm` points at `edit`, not at `edit_product`:

```python
edit = WebFunction(edit_product, slug="edit-product")


def select_product(
    product_id: int,
) -> Annotated[Product, OpenForm(edit, hidden=("product_id",))]:
    return database.product(product_id)


router_of([select_product, edit])
```

The lookup is neither by slug nor by callable, so another equivalent instance
does not work: it describes the same thing, but it is not the one the `OpenForm`
points at.

```python
router_of([
    select_product,
    WebFunction(edit_product, slug="edit-product"),
])
# ReturnContractError: OpenForm target is not registered in this space
```

A matching slug does not prove it is the same function, and linking by slug
could silently open a different one.

The **space** is what resolves the target, not the `WebFunction` that declares
the `OpenForm`: a function on its own cannot know what else is registered, and
only the space can tell a missing target from an ambiguous one. That is why the
two cases are different errors, and why the target is compared by identity.

The names in `hidden` are validated there too, once the target's parameters are
known:

```text
ReturnContractError: unknown hidden field 'nope' for OpenForm target 'edit-product'
```

## What you can return

A dataclass — meaning its declared fields — or a mapping, which is copied with
`dict(value)`. The prefill can be **partial**: the parameters that do not appear
keep their declared default. Any other value, such as a string, a number, a list
or `None`, is a return error:

```text
ReturnContractError: OpenForm return must be a mapping or dataclass instance
```

The returned values go through the target function's schema, exactly like a
prefill received by URL: that is how unknown keys, types, constraints, enums,
dates and nested dataclasses are checked, and how they are converted for the
browser transport. There is no second validation system.

### Chaining a file

A function that receives a file can pass it on to the next one: the file reaches
the function as a local path, and the function hands that same local path back.

```python
from func_to_web import IsPathFile

DocumentPath = Annotated[str, IsPathFile()]


def pick(document: DocumentPath) -> Annotated[dict, OpenForm(describe)]:
    return {"document": document}
```

What travels in the `href` is not that path but the file's reference, and the
target form opens with the file already in place and no upload pending. The
condition is that the file is still in storage: a file the function wrote
somewhere else (its own temporary directory, for example) has no reference, so
the execution fails before the `href` is built and nothing goes out:

```text
500 {"error": "ReturnContractError: OpenForm returned a file outside the storage directory: 'draft.txt'"}
```

The message names the file, not where it was. See [files.md](files.md) and
[security.md](security.md).

If the values are not valid as prefill, the failure belongs to the function's
**return**, not to the user's input, so the request answers `500` with the
original exception as its cause:

```text
500 {"error": "ReturnContractError: OpenForm returned invalid prefill: unknown prefill field: 'nope'"}
500 {"error": "ReturnContractError: OpenForm returned invalid prefill: product_id: default: expected int, got str"}
```

## What reaches the browser

One more output, with the URL of the form to open:

```json
{"result": {"type": "form", "href": "../edit-product/?prefill=%7B…%7D&hidden=%5B…%5D"}}
```

The URL is **relative**, like `../static` and `../returns`, so it works under
any `prefix`, and it uses the usual query string. There is no second prefill
protocol, no prefill stored on the server, and no tokens: opening the target is
an ordinary request to `GET /{slug}/`.

The web interface navigates to that URL in the same tab, and it also shows the
link in case the browser does not follow it. Over SSE the flow does not change:
`start`, whatever `print` output there is, and then the `result` carrying this
output.

## Limits

`OpenForm` can only mark the **whole** return, and only once; a tuple, a list, a
union or two marks in different annotations are rejected when the `WebFunction`
is built:

```text
ReturnContractError: OpenForm can only mark the whole return, and only once
```

Two marks inside the **same** `Annotated` are rejected before that count is
reached, with a different message:

```text
ReturnContractError: an Annotated cannot carry more than one OpenForm
```

It does not combine with `Download`, so the only result of calling a function
marked with `OpenForm` is the form opening, and navigation is always in the
same tab. The prefill travels in the URL, with the limits described in
[prefill.md](prefill.md): it is not a place for secrets, and `hidden` hides but
does not authorize. See [limitations.md](limitations.md) and
[security.md](security.md).

Related: [prefill.md](prefill.md), [outputs.md](outputs.md),
[web-function.md](web-function.md).
