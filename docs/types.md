# Types and validation

The catalog of types and constraints is defined by
[`pytypehint`](https://github.com/offerrall/pytypehint); FuncToWeb does not
extend or reinterpret it, and that project's repository is the complete
reference. This document describes what that contract guarantees and how it
reaches the web.

FuncToWeb re-exports every piece, so you never have to import from the lower
layers: the constraint atoms (`Min`, `Max`, `Choices`, `MultipleOf`, `Pattern`,
`IsPathFile`), the annotation atoms (`Label`, `Description`, `Placeholder`,
`Step`, `Slider`, `IsPassword`, `Rows`, `Extra`, `OptionalToggle`), the
convenience types (`Color`, `Email`) and the errors (`SchemaTypeError`,
`SchemaValueError`).

## The annotation is the contract

Type hints compile to a schema that validates every value **before** the
function is called.

```python
from typing import Annotated

from func_to_web import Max, Min


def percentage(value: Annotated[int, Min(0), Max(100)]) -> int:
    return value
```

`value` is exactly an `int` between 0 and 100: the function never runs with
`-1`, `101`, `1.5`, `"50"` or `True`. FuncToWeb does not validate anything
itself; it builds the arguments with the schema and lets the core reject
whatever does not comply.

## Validation is recursive

Recursive validation reaches every element of a structure, not just its outer
shape. In a list, the outer constraints belong to the list and the inner ones to
each element, and both apply:

```python
def average(
    values: Annotated[
        list[Annotated[int, Min(0), Max(100)]],
        Min(1),
        Max(20),
    ],
) -> float:
    return sum(values) / len(values)
```

Between 1 and 20 values, each one between 0 and 100. In the interface, `list[T]`
is a list of widgets with an **Add** button and a trash icon on each row, and
the length limits are the ones declared on the list.

## Dataclasses

A dataclass used as a parameter compiles to a nested structure and reaches the
function as a real instance, already validated. You do not have to inherit from
a base model or register any types.

```python
from dataclasses import dataclass


@dataclass
class Limits:
    minimum: int
    maximum: int


def configure(limits: Limits) -> str:
    return f"{limits.minimum} - {limits.maximum}"
```

Nesting is not a special case: a dataclass can contain other dataclasses, lists
of dataclasses or unions, and recursive validation reaches into all of them.

## Unions and optionals

A union offers several possible shapes for the same parameter, and the transport
identifies the chosen branch, using `$type` when that is needed to avoid
guesswork (see [http.md](http.md)).

An `X | None` parameter is optional: the interface represents it with a toggle
that decides whether the value travels.

## Defaults

Defaults are validated when the schema is compiled and **rematerialized** on
every execution, so a mutable default (a list, a dataclass) is never shared
between calls:

```python
@dataclass
class Item:
    value: int


def process(items: list[Item] = [Item(1), Item(2)]) -> int:
    return sum(item.value for item in items)
```

Every execution receives a new, validated structure, even when the default
contains lists or nested dataclasses. A [prefill](prefill.md) is applied as a
temporary default for that one form opening, which is why its errors arrive with
the `default:` prefix.

## Convenience types

These are not new types. `Color` is a `str` with a hexadecimal pattern: Python
receives a `str`, the core validates the format and the browser shows a color
picker. Writing the same pattern by hand gives you the same validation and the
same widget; what changes is the message: `Color` comes with
`Hex color like #ff5733`, while a hand-written pattern falls back to
`Invalid format`.

```python
from func_to_web import Color


def set_color(color: Color) -> str:
    return color
```

`Email` works the same way with its own pattern, and both are imported from
`func_to_web` alongside `COLOR_PATTERN` and `EMAIL_PATTERN`.

A `str` annotated with `IsPathFile(...)` declares a file reference with its
accepted extensions and, optionally, its size limits; the full contract is in
[files.md](files.md).

## What happens when the contract is broken

A value that breaks the contract fails before it enters the function. Over HTTP
that is a `422` with the message from the core; in a prefill, a `400`. See
[http.md](http.md) and [prefill.md](prefill.md).

## Seeing every control

The widgets are `pytypehintweb`'s, and that project ships a demo with the
complete catalog: every control, grouped by type, with the cases each one
covers.

```bash
pip install "pytypehintweb[demo]"
pytypehintweb-demo
```

![The widget catalog, grouped by type, with the cases of each one](images/pytypehintweb-demo.png)

It answers the question this page cannot answer in prose —what a given
annotation actually looks like— so it is the fastest way to choose between two
that validate the same thing. `Choices` on a `str` against a `Pattern`,
`Slider` against a plain `int`, `Rows` against a single-line field: the
difference is visual, and it is easier to see it than to read it.

Related: <https://github.com/offerrall/pytypehint>, [files.md](files.md),
[architecture.md](architecture.md).
