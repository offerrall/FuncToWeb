from collections.abc import Callable
from typing import Any

Relative = Callable[[tuple[str, ...], str], str]


def with_references(plan: dict[str, Any], relative: Relative) -> dict[str, Any]:
    """Rewrite every file default of plan as a reference, in place.

    relative receives the coordinates of the field and the local path the plan
    would publish, and returns what travels in its place; raising is how it
    refuses a file the storage does not own. The plan is the only source of
    what a file field is, so this reaches one at any depth.

    In place: plan must be one plan_of() has just built and nobody else holds
    yet. A published plan is read-only —WebFunction.plan above all, which the
    page, the index and /doc share— so it never comes here; the callers pass a
    plan on its way to becoming one, or a temporary plan of their own.

    The question is where the file defaults are. Whether a space needs /upload
    is a different one, about controls rather than defaults, and
    models.functions.has_file() answers it with a walk of its own that reads
    any shape of plan instead of knowing this grammar.
    """
    _fields(plan["fields"], (), relative)

    return plan


def _fields(
    fields: list[dict[str, Any]],
    where: tuple[str, ...],
    relative: Relative,
) -> None:
    for field in fields:
        coordinates = (*where, field["name"])

        _node(field["node"], coordinates, relative)

        if "default" in field:
            field["default"] = _default(field["node"], field["default"],
                                        coordinates, relative)


def _node(
    node: dict[str, Any],
    where: tuple[str, ...],
    relative: Relative,
) -> None:
    kind = node["kind"]

    if kind == "object":
        _fields(node["fields"], where, relative)
    elif kind == "list":
        _node(node["item"], where, relative)
    elif kind == "optional":
        _node(node["node"], where, relative)
    elif kind == "choice":
        for branch in node["branches"]:
            _node(branch["node"], where, relative)


def _default(
    node: dict[str, Any],
    value: Any,
    where: tuple[str, ...],
    relative: Relative,
) -> Any:
    if value is None:
        return None

    kind = node["kind"]

    if kind == "optional":
        return _default(node["node"], value, where, relative)

    if kind == "choice":
        branch = node["branches"][value["branch"]]["node"]

        return {"branch": value["branch"],
                "value": _default(branch, value["value"], where, relative)}

    if kind == "file":
        if node["options"]["multiple"]:
            return [relative(where, item) for item in value]

        return relative(where, value)

    if kind == "object":
        return {field["name"]: _default(field["node"], value[field["name"]],
                                        (*where, field["name"]), relative)
                for field in node["fields"]}

    if kind == "list":
        return [_default(node["item"], item, where, relative)
                for item in value]

    return value
