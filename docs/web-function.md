# `WebFunction` and `WebFunctions`

```text
WebFunction  = a prepared web function
WebFunctions = a prepared space of functions
```

Both are imported from `func_to_web` and are used by
[`page_of()`](prefill.md), [`app_of()`](router.md) and [`run()`](run.md).
Preparing them by hand is optional: the last two build whatever is missing from
the individual functions you pass in.

## `WebFunction`

```python
WebFunction(
    fn,
    name="",
    description="",
    slug="",
    capture_prints=None,
)
```

`fn` is a plain Python function with its type hints. Bound methods,
`functools.partial` and objects with `__call__` are not supported, but they do
not all fail in the same place:

| Callable | Where it fails |
| --- | --- |
| a bound method | it has `__name__`, so it reaches the core, which rejects it while compiling the schema and asks you to wrap the call in a normal function |
| a `partial`, an object with `__call__` | no `__name__`: without an explicit `name=` and `slug=` they fail earlier, while deriving the metadata |
| either of those two, with `name=` and `slug=` written out | the core's rejection, the same one the bound method gets |

```python
WebFunction(functools.partial(add, 1))
# TypeError: fn must have a non-empty string __name__ when name or slug
# is not provided
```

`WebFunction` does not modify the function; it only reads it.

### Derived metadata

The three metadata fields are optional, and `""` always means "derive it":

| Field | With no value it is derived from | If that is not possible |
| --- | --- | --- |
| `name` | `fn.__name__` | `TypeError` |
| `description` | `fn.__doc__`, or `""` if there is none | — |
| `slug` | `fn.__name__` | `TypeError` or `ValueError` |

Since `""` is the signal to derive, a function with a docstring cannot be
published with an empty description. The slug always comes from `fn.__name__`,
never from `name`: passing `name="Account signup"` does not change the slug.

`name` is stored with `strip()` and cannot end up empty; beyond that it is free
text. `description` is normalized with `inspect.cleandoc()` and a final
`strip()`, whether it comes from the docstring or from the parameter, for
portability across Python versions
([design/web-function.md](design/web-function.md)). The text keeps its line
breaks, which are carried unchanged inside the plan; the [`/doc`](api-docs.md)
index writes the description on the same line as the slug, so a single-line
description looks better there.

Both must be `str`; any other type raises a `TypeError`, as does an `fn.__doc__`
that is neither `str` nor `None`.

### The name is formatted when it is displayed

Wherever the name is displayed to be read, it gets a minimal touch-up: `_`
characters become spaces and only the **first** letter is uppercased. Those are
the three places it appears — the page's `<title>` and `<h1>`, and the link in
the [space index](run.md#the-space-index).

```text
blur_image        → Blur image
read_HTML_pages   → Read HTML pages
my_report         → My report
```

It is **presentation only**. `WebFunction.name` stores what it was given, with
the `strip()` above as its only normalization, and that is what appears in the
plan `/doc` publishes, and what any code that reads the attribute sees:

```python
WebFunction(blur_image).name   # 'blur_image', not 'Blur image'
```

If you want full control over the heading, write it out: `name="Blur image"`.
See [design/web-function.md](design/web-function.md).

### Slug

A single URL segment: letters, digits, underscores and single hyphens, with no
leading or trailing hyphen. `doc`, `static`, `upload` and `returns` are reserved
because they are routes of the space itself. They are always rejected, even in a
space that never registers `/upload` or `/returns`: the contract does not depend
on the order in which the routes are declared.

Without `slug=` it is `fn.__name__` **as it is**, with no transformation: the
function you wrote is the URL you get.

```text
save_result   → save_result
load__cache   → load__cache
__dunder__    → __dunder__
MyFunction    → MyFunction
<lambda>      → ValueError: cannot derive a valid slug from
                fn.__name__='<lambda>'; pass slug explicitly
```

A name that is not a valid segment —`<lambda>` and anything outside letters,
digits and underscores— is refused rather than repaired, and asks for an
explicit `slug=`.

Slugs are case-sensitive, as URLs are: `/MyTool/` and `/mytool/` are different
routes.

A hand-written `slug=` is **not silently normalized** either: it is validated as
written, so `"-hello"`, `"hello--world"` or `" add "` are errors rather than
being turned into something similar. `strip()` is not applied to it, precisely
so that a stray space is caught. Hyphens are still accepted there, which is how
a function keeps a hyphenated URL: `slug="edit-product"`.

### `capture_prints`

An execution policy, not a data contract: it decides whether what the function
prints is streamed over [`/invoke-stream`](streaming.md). `None` means
inheriting whatever the space decides.

### Computed fields

On construction it compiles three fields that are part of the public contract
and can be read: `schema`, the core's `Signature`; `plan`, the web plan the
browser consumes and `/doc` publishes; and `html`, the base page. Together with
the already normalized metadata, they are everything `page_of()`, `app_of()`
and `/doc` need.

`schema` is exactly what the core returns, with `fn.__name__` and the docstring
untouched. `plan` is an enriched copy: its `name` and `description` are those of
the `WebFunction`, so the page, the index and `/doc` always publish the same
declared metadata, and every file default is written as its
[reference](files.md), never as the path the schema holds.

An inconsistent definition fails right there, at startup. Without prefill,
requests return that HTML from memory; with prefill, a temporary plan and
temporary HTML are generated without touching the base ones. See
[prefill.md](prefill.md).

### Immutability

The dataclass is `frozen`: reassigning an attribute raises
`FrozenInstanceError`, and that covers the computed fields too. **The freeze is
not deep**: `plan` is an ordinary `dict` and nothing stops you from mutating its
contents, which are read-only by contract. The same object is shared with
`/doc`, so modifying it would change what the whole space sees.

## `WebFunctions`

```python
from func_to_web import WebFunction, WebFunctions


space = WebFunctions(
    (
        WebFunction(add),
        WebFunction(divide, name="Divide numbers", slug="division"),
    ),
    title="Internal tools",
)
```

You prepare it by hand when you want to reuse or inspect the space before
mounting it.

`functions` must be exactly a **tuple** of `WebFunction`; nothing is wrapped
automatically here:

| Input | Error |
| --- | --- |
| a list or a generator | `TypeError: functions must be tuple` |
| an entry that is not a `WebFunction` | `TypeError: functions must contain only WebFunction instances` |
| the empty tuple | `ValueError: at least one function is required` |
| two entries with the same slug | `ValueError: two functions share the slug 'add'` |

The last one covers registering the same `WebFunction` twice.

The slug is a function's identity inside the space: it is its route and what
`/doc` and the index use to name it.

`title` names the space. It must be `str`, is stored with `strip()` and cannot
end up empty; if it is omitted, the title is `"FuncToWeb"`. An already prepared
space carries its own title, so passing one again to `app_of()` or `run()` is
a `TypeError`, not an override that wins.

`document` is the text `/doc` serves, generated once when the space is built.
See [api-docs.md](api-docs.md).

The dataclass is `frozen` and keeps no mounting state, with the same
immutability caveat as `WebFunction`: the same space can be mounted in several
applications, and none of them alters it.

```python
app.mount("/a", app_of(space))
other_app.mount("/b", app_of(space))
```

Related: [router.md](router.md), [run.md](run.md), [prefill.md](prefill.md),
[api-docs.md](api-docs.md).
