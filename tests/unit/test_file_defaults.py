import json

import pytest

from shared import Attachment
from func_to_web import WebFunction, page_of
from func_to_web.models.file_defaults import with_references
from func_to_web.models.function import build_prefill
from func_to_web.web.upload import stored_file as resolve_reference

ABSENT = object()


def read_attachments(rows: list[Attachment]) -> str:
    return "ok"


def file_node(*, multiple=False):
    return {"kind": "file", "options": {"multiple": multiple}}


def field_node(name, node, default=ABSENT):
    field = {"name": name, "node": node}

    if default is not ABSENT:
        field["default"] = default

    return field


def object_node(*fields):
    return {"kind": "object", "fields": list(fields)}


def list_node(item):
    return {"kind": "list", "item": item}


def optional_node(node):
    return {"kind": "optional", "node": node}


def choice_node(*nodes):
    return {"kind": "choice", "branches": [{"node": node} for node in nodes]}


def plan_of_fields(*fields):
    return {"v": 1, "kind": "form", "fields": list(fields)}


def recorder():
    seen = []

    def relative(where, path):
        seen.append((where, path))
        return f"ref:{path}"

    return seen, relative


def rewritten(plan):
    seen, relative = recorder()
    return with_references(plan, relative), seen


def defaults_of(plan):
    return {field["name"]: field.get("default", ABSENT)
            for field in plan["fields"]}


def test_a_file_default_on_a_root_field_becomes_a_reference():
    plan = plan_of_fields(field_node("document", file_node(), "a.txt"))

    result, seen = rewritten(plan)

    assert defaults_of(result)["document"] == "ref:a.txt"
    assert seen == [(("document",), "a.txt")]


def test_a_file_default_inside_an_object_becomes_a_reference():
    plan = plan_of_fields(
        field_node("row", object_node(field_node("document", file_node())),
                   {"document": "a.txt"}),
    )

    result, seen = rewritten(plan)

    assert defaults_of(result)["row"] == {"document": "ref:a.txt"}
    assert seen == [(("row", "document"), "a.txt")]


def test_a_file_default_inside_a_list_becomes_a_reference():
    plan = plan_of_fields(
        field_node("documents", list_node(file_node()), ["a.txt", "b.txt"]),
    )

    result, seen = rewritten(plan)

    assert defaults_of(result)["documents"] == ["ref:a.txt", "ref:b.txt"]
    assert seen == [(("documents",), "a.txt"), (("documents",), "b.txt")]


def test_a_file_default_behind_an_optional_item_becomes_a_reference():
    plan = plan_of_fields(
        field_node("documents", list_node(optional_node(file_node())),
                   ["a.txt"]),
    )

    result, seen = rewritten(plan)

    assert defaults_of(result)["documents"] == ["ref:a.txt"]
    assert seen == [(("documents",), "a.txt")]


def test_a_file_default_inside_a_choice_branch_becomes_a_reference():
    plan = plan_of_fields(
        field_node("mixed", choice_node({"kind": "int"}, file_node()),
                   {"branch": 1, "value": "a.txt"}),
    )

    result, seen = rewritten(plan)

    assert defaults_of(result)["mixed"] == {"branch": 1, "value": "ref:a.txt"}
    assert seen == [(("mixed",), "a.txt")]


def test_a_default_on_the_other_choice_branch_is_left_alone():
    plan = plan_of_fields(
        field_node("mixed", choice_node({"kind": "int"}, file_node()),
                   {"branch": 0, "value": 3}),
    )

    result, seen = rewritten(plan)

    assert defaults_of(result)["mixed"] == {"branch": 0, "value": 3}
    assert seen == []


def test_a_multiple_file_default_rewrites_every_path():
    plan = plan_of_fields(
        field_node("documents", file_node(multiple=True), ["a.txt", "b.txt"]),
    )

    result, seen = rewritten(plan)

    assert defaults_of(result)["documents"] == ["ref:a.txt", "ref:b.txt"]
    assert seen == [(("documents",), "a.txt"), (("documents",), "b.txt")]


def test_a_file_default_in_an_object_nested_in_an_object_is_reached():
    plan = plan_of_fields(
        field_node(
            "outer",
            object_node(field_node(
                "middle",
                object_node(field_node("document", file_node())),
            )),
            {"middle": {"document": "a.txt"}},
        ),
    )

    result, seen = rewritten(plan)

    assert defaults_of(result)["outer"] == {"middle": {"document": "ref:a.txt"}}
    assert seen == [(("outer", "middle", "document"), "a.txt")]


def test_a_default_declared_on_a_nested_object_field_is_reached():
    plan = plan_of_fields(
        field_node("row", object_node(
            field_node("document", file_node(), "a.txt"),
        )),
    )

    result, seen = rewritten(plan)

    inner = result["fields"][0]["node"]["fields"][0]

    assert inner["default"] == "ref:a.txt"
    assert seen == [(("row", "document"), "a.txt")]


def test_an_object_appends_its_field_name_to_the_coordinates():
    plan = plan_of_fields(
        field_node("row", object_node(field_node("document", file_node())),
                   {"document": "a.txt"}),
    )

    _, seen = rewritten(plan)

    assert [where for where, _ in seen] == [("row", "document")]


def test_a_list_does_not_append_to_the_coordinates():
    plan = plan_of_fields(
        field_node("documents", list_node(list_node(file_node())),
                   [["a.txt"], ["b.txt"]]),
    )

    _, seen = rewritten(plan)

    assert [where for where, _ in seen] == [("documents",), ("documents",)]


def test_a_list_of_objects_appends_only_the_object_field_name():
    plan = plan_of_fields(
        field_node("rows",
                   list_node(object_node(field_node("document", file_node()))),
                   [{"document": "a.txt"}, {"document": "b.txt"}]),
    )

    _, seen = rewritten(plan)

    assert [where for where, _ in seen] == [("rows", "document"),
                                            ("rows", "document")]


def test_a_callback_that_raises_propagates_uncaught():
    def angry(where, path):
        raise RuntimeError("refused")

    plan = plan_of_fields(field_node("document", file_node(), "a.txt"))

    with pytest.raises(RuntimeError) as error:
        with_references(plan, angry)

    assert str(error.value) == "refused"


def test_a_plan_with_no_file_nodes_never_calls_the_callback():
    plan = plan_of_fields(
        field_node("title", {"kind": "str"}, "hola"),
        field_node("tags", list_node({"kind": "str"}), ["a", "b"]),
        field_node("row", object_node(field_node("city", {"kind": "str"})),
                   {"city": "Madrid"}),
    )

    result, seen = rewritten(plan)

    assert seen == []
    assert defaults_of(result) == {"title": "hola", "tags": ["a", "b"],
                                   "row": {"city": "Madrid"}}


def test_a_field_with_no_default_key_never_calls_the_callback():
    plan = plan_of_fields(field_node("document", file_node()))

    result, seen = rewritten(plan)

    assert seen == []
    assert "default" not in result["fields"][0]


def test_a_none_default_on_a_file_field_never_calls_the_callback():
    plan = plan_of_fields(field_node("document", file_node(), None))

    result, seen = rewritten(plan)

    assert seen == []
    assert defaults_of(result)["document"] is None


def test_a_none_item_in_an_optional_position_never_calls_the_callback():
    plan = plan_of_fields(
        field_node("documents", list_node(optional_node(file_node())),
                   ["a.txt", None]),
    )

    result, seen = rewritten(plan)

    assert seen == [(("documents",), "a.txt")]
    assert defaults_of(result)["documents"] == ["ref:a.txt", None]


def test_a_none_field_of_an_object_default_never_calls_the_callback():
    plan = plan_of_fields(
        field_node("row", object_node(
            field_node("document", file_node()),
            field_node("tag", {"kind": "str"}),
        ), {"document": None, "tag": "z"}),
    )

    result, seen = rewritten(plan)

    assert seen == []
    assert defaults_of(result)["row"] == {"document": None, "tag": "z"}


def test_the_plan_is_rewritten_in_place():
    plan = plan_of_fields(field_node("document", file_node(), "a.txt"))
    _, relative = recorder()

    result = with_references(plan, relative)

    assert result is plan
    assert plan["fields"][0]["default"] == "ref:a.txt"


def test_serving_a_prefilled_page_leaves_the_web_function_plan_untouched(
        stored_file):
    stored_file("a.txt")
    web_function = WebFunction(read_attachments)
    before = json.dumps(web_function.plan, sort_keys=True)
    values = build_prefill(web_function.schema,
                           {"rows": [{"document": "a.txt"}]},
                           file_resolver=resolve_reference)

    page_of(web_function, prefill=values)

    assert json.dumps(web_function.plan, sort_keys=True) == before
    assert defaults_of(web_function.plan)["rows"] is ABSENT


def test_plan_of_hands_out_a_fresh_plan_every_time():
    """The one assumption with_references makes about a library it does not own.

    Rewriting in place is safe only because nobody else is holding the plan,
    and that rests entirely on plan_of() building a new one per call —
    labelled_plan() copies the mapping but not the list underneath it.
    """
    from pytypehintweb import plan_of

    schema = WebFunction(read_attachments).schema

    first = plan_of(schema)
    second = plan_of(schema)

    assert first == second
    assert first is not second
    assert first["fields"] is not second["fields"]
    assert first["fields"][0] is not second["fields"][0]
