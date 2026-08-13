"""A plan default written the way a browser submit writes the same value.

Two representations of one value meet here. `plan_of()` publishes a default in
the plan's own grammar, which the widgets read to decide what to show: a union
default arrives as `{"branch": index, "value": ...}`, because a plan describes
controls and the index names the control the page opens on. What travels back
when that page is submitted is a different document — the portable transport
`decode()` reads — and there the branch is named the way the value itself can
carry it, or not named at all.

Everything else agrees between the two, so only a union is converted, and the
conversion is the plan's own answer rather than a rule restated here: each
branch carries the `mode` pytypehintweb already decided for it and the `value`
that is its option id. What the three modes emit is form.js `compileChoice`,
which is the definition of what the browser sends:

    wrapped -> {"$type": <option id>, "$value": <value>}
    inline  -> {"$type": <option id>, **<fields>}
    plain   -> <value>

So a union with a single non-None branch — `X | None` — never reaches this at
all: `plan_of()` compiles no choice node for it and its default is already the
value, exactly as the browser would send it.
"""

from typing import Any

from pytypehintweb import INLINE, WRAPPED

# The reserved keys of the discriminated transport, mirrored from form.js the
# same way pytypehintweb mirrors them from the core. A field can never collide
# with them: field names must be identifiers, and neither of these is one.
_TYPE = "$type"
_VALUE = "$value"


def as_submitted(node: dict[str, Any], default: Any) -> Any:
    """default, read through its plan node, as the browser would submit it.

    node is the "node" of the field the default belongs to, and default the
    "default" plan_of() published beside it — after any rewriting the caller
    does of its own, file references above all, which happens in the plan's
    grammar and leaves the union representation as it found it.

    The result is transport, so it is what decode() takes and never what a
    plan carries: a caller putting it back into a plan would be handing the
    widgets a document they cannot read.
    """
    if default is None:
        # An optional left empty. The plan writes the None before choosing a
        # branch, so nothing below is a union representation, and a submit
        # sends the same null.
        return None

    kind = node["kind"]

    if kind == "optional":
        return as_submitted(node["node"], default)

    if kind == "choice":
        branch = node["branches"][default["branch"]]
        value = as_submitted(branch["node"], default["value"])

        if branch["mode"] == WRAPPED:
            return {_TYPE: branch["value"], _VALUE: value}

        if branch["mode"] == INLINE:
            return {_TYPE: branch["value"], **value}

        return value

    if kind == "object":
        return {field["name"]: as_submitted(field["node"],
                                            default[field["name"]])
                for field in node["fields"]}

    if kind == "list":
        return [as_submitted(node["item"], item) for item in default]

    # Every leaf — including a file node, whose default is already the bare
    # reference the widget shows and sends back untouched, one of them or a
    # list of them when it is `multiple`.
    return default
