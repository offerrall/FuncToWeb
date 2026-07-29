# What changed underneath, from 1.6 to 2.0

Why 2.0 breaks what it breaks. The migration itself — the equivalence tables and
the update steps — is in
[migration-1.6-to-2.0.md](../migration-1.6-to-2.0.md).

Almost everything the migration lists has the same root cause: the two layers
FuncToWeb rests on were rewritten, and that widened what you can write in a
signature.

## The type core: from `pytypeinput` to `pytypehint`

`pytypeinput` 1.0.2 reduced every parameter to **a single scalar** of six types
(`int`, `float`, `str`, `bool`, `date`, `time`), with flat metadata alongside it
and pydantic behind it; anything composite was flattened by hand inside
FuncToWeb. `pytypehint` 0.0.7 compiles the signature into a tree of shapes:
nesting becomes the norm.

### Impossible before, possible now

| Capability | 1.6 | 2.0 |
| --- | --- | --- |
| dataclass as a parameter type | `Unsupported type: Address. Must be one of: str, time, float, int, bool, date` | first-class type |
| dataclass inside a dataclass | `Nested Params are not supported: field 'addr' of 'Person' is a Params class. Flatten the fields into one class or pass them as separate parameters.` | no depth limit |
| optional dataclass | `Optional Params are not supported: parameter 'p' is 'Address \| None'. A Params group cannot be toggled off; make individual fields optional inside the class instead.` | `Address \| None` |
| `list[dataclass]`, dataclass with a list of dataclasses | no | yes |
| `list[list[int]]` | `Nested lists are not supported (list[list[...]])` | at any depth |
| union of real types | only `X \| None`; with three branches, `Union cannot have more than 2 types, got 3` | any number of branches |
| union of dataclasses, `list[Circle \| Square]` | no | yes, discriminated by `$type` |
| multiples, file size, third-party metadata | `Field(multiple_of=)` was silently discarded; only the file's extension was checked | `MultipleOf`, `IsPathFile(min_size=…, max_size=…)`, `Extra("package.key", …)` |
| empty list / inconsistent schema | `List cannot be empty (use list[...] \| None for optional lists)`; an impossible range was accepted and then failed on every value | an empty list is valid unless `Min` says otherwise; `Int: empty range (10..5)` at compile time |
| mutable defaults | shared, as in plain Python | fresh on every execution |

The 1.6 errors that come out of `analyze_type` are prefixed with the field name:
`[direccion] Unsupported type: Address. Must be one of: str, time, float, int,
bool, date`. The two `Params` errors do not: FuncToWeb raises them as
`ValueError`, with no prefix.

The last row applies without touching the signature: a default is a recipe that
is rematerialized every time the key is missing, and that is guaranteed at
compile time.

```python
def acc(xs: list[int] = []):
    xs.append(1)
    return xs
# direct call       [1] [1, 1] [1, 1, 1]   — the list from the def
# through 2.0       [1] [1]    [1]         — a new list per call
```

### What was lost

**Coercion.** `pytypeinput` converted `"42"` → `42`, `"2024-01-15"` → `date`,
`"true"` → `True` and `3` → `3.0`. `pytypehint` compares the exact type (`expected
int, got str`): converting is the web layer's job. `Dropdown` and its
`refresh_choices()` are gone, as are `Label`/`Description` on a list item (1.6
propagated them to the list; today you get `field atoms cannot apply to list
items`) and the entry points `analyze_pydantic_model`, `analyze_dataclass` and
`analyze_class_init`: only `signature_of(fn)` and `struct_of(cls)` remain.
Lambdas, `*args` and a parameter with no hint now raise errors, whereas 1.6
skipped them silently. An empty `str` is now valid.

**Bound methods** are a different matter: 1.6 served them (`GET /` returned `200`
and submitting returned `{"success": true, "type": "text", "data": "hola"}`), and
2.0 rejects them when building the `WebFunction`: `expected a plain function, got
<bound method …> — bound methods, partials and callable objects are not
supported: wrap the call in a plain function`. This is lost functionality, not a
silent failure that is now reported: you have to wrap the call in a plain
function.

### Validation and arguments

The errors are `SchemaTypeError` and `SchemaValueError`, subclasses of
`TypeError` and `ValueError`, carrying the location as data (`.path`) and the
failing leaf (`.leaf`); one line instead of pydantic's block: `t: members:
[0]: address: street: expected str, got int`. What the function receives also
changes: 1.6 validated field by field, each one a scalar, and FuncToWeb
reassembled the `Params` from the flat fields; 2.0 passes a dict to
`Signature.build()`, which validates the whole tree and returns kwargs with real
instances at their proper depth, with their defaults resolved and their
`__post_init__` already run.

## The web layer: from `pytypeinputweb` to `pytypehintweb`

1.6 served a web component: two bundles (`get_js()`/`get_css()`), a Jinja2 template with
`<pti-form params='…'>` and a **flat** list of `ParamMetadata`. 2.0 compiles a **plan**
(`plan_of(fn)`, a JSON dict with `"v": 1`) and embeds it in a Jinja-free page that the ES
modules in `STATIC` read with `compileForm()`. The contract stops being a custom element
and becomes data, versioned and checkable in Python without a browser; `jinja2` and
`python-multipart` drop out of the dependencies.

| 1.6 | 2.0 |
| --- | --- |
| `get_js()`, `get_css()`, `list_css_variables()` | `STATIC`: unbundled ES modules, no build step |
| `<pti-form>`: `load()`, `getValues()`, `reset()` | `compileForm(plan)`: `fields`, `read()`, `uploads()`, `isReady()`, `onChange()` |
| — | `decode()`, `WebConfig` |

| Control | 1.6 | 2.0 |
| --- | --- | --- |
| text, number, bool, date, time, color, dropdown | yes | yes |
| slider, password, textarea | yes | yes, but `Slider` only on `int` |
| file picker | yes | yes; `list[File]` is **one** multi-file control |
| optional toggle | yes | yes, and per list item too |
| dynamic list with add/remove | one level, scalars only | on any node |
| `list[list[...]]`, nested dataclass | no | `list → list`, an `object` node at any depth |
| union of real types with a branch selector | no | `choice` node |
| enum as a node of its own | no | yes; it is sent by member name |
| web interface texts | hard-coded in the JS | `WebConfig`, 37 templates |

Nesting is the big jump: `analyze_type` rejected `list[list[int]]` (`Nested lists
are not supported`), any dataclass (`Unsupported type: Punto`) and every union without
`None`, and 1.6 papered over it by **flattening** the `Params`. Today `list[list[Punto]]`
gives `list → list → object`.

### Transport, theme and prefill

`decode(schema, data, file_resolver=…)` is the inbound half that 1.6 did not have: it
prepares the JSON before building (`3` → `3.0` where the shape is `float`, ISO →
`date`/`time`, name → enum member, reference → host path) and resolves the `$type`/`$value`
of the unions that collide in a single JSON type (`str | date` and `int | float` are sent
wrapped; `Punto | Circulo`, with `$type` inside the object).

The server sets the theme with `data-pth-theme` on the page itself, so it does not
flash. **Customization is lost:** `widgets.css` defines 100 `--pth-*` tokens (154
declarations, counting the dark-mode ones), but there is no
`list_css_variables()` and no slot for a stylesheet of your own. And the plan is static:
no dynamic options.

Prefill lives here: a proposed value is the plan's `default`, at any depth
(`{"x": 1, "y": 2}`, `{"branch": 1, "value": "hola"}`, an ISO date, an enum name, a file
reference). Hidden fields are applied by FuncToWeb, but only because the layer exposes
`form.fields`.

### Confirmed limits of the adapter

- `Slider` on `float`: `Float.slider is not supported yet`. On `int` it requires `Min` and `Max`.
- `Pattern` is restricted to the portable subset: `\d`, `\w`, `\s`, `\b` and the unescaped dot are rejected.
- Combinations that would need different controls: `Rows`+`Choices`, `Rows`+`IsPassword`, `Slider`+`Placeholder`, `Choices`+`Placeholder`, `Choices`+`Slider`.
- Forbidden presentation atoms: the text-related ones alongside `IsPathFile` (`Str.pattern with IsPathFile is not supported yet`, and likewise `placeholder`, `rows`, `min`, `max`, `choices`, `is_password`), and `Label`/`Description` on a list item (`field atoms cannot apply to list items`; `Placeholder` does pass).
- `Extra` is stored by the core but the layer does not emit it; the `enum` node reserves `labels: null` and shows the raw names.
- Integers outside JavaScript's safe range (±2⁵³−1) and a dataclass with no fields: `TypeError` when compiling the plan.
- A recursive dataclass is compiled by the core, but it breaks the plan: `RecursionError: maximum recursion depth exceeded` when building the `WebFunction`.

## Defaults that changed on purpose

**`host` no longer listens on the whole network.** 1.6 started on `0.0.0.0`,
exposed to the local network from the very first run; 2.0 listens only on the
loopback interface. FuncToWeb provides no authentication, so the old behavior
now has to be requested explicitly:

```python
run(fns, host="0.0.0.0")
```

**`root_path` is gone.** In 1.6 the internal URLs came from each request's
`root_path`, and behind a proxy you had to pass it to Uvicorn; in 2.0 every URL
is relative (`../static/page.css`, `invoke-stream`) and works under any mounted
prefix.

**The slug no longer depends on the name.** 1.6 did
`func_name.replace("_", " ").capitalize()` and derived the slug from that name;
2.0 uses `__name__` as is for both. The difference is in the **attribute**: for
`def my_function`, 1.6 gave `name="My function"` and 2.0 gives
`name="my_function"`, but the `<title>`, the `<h1>` and the `run()` index still
show `My function`, because the page applies the same prettifying at display
time.
