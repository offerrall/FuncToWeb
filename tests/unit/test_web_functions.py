import re
from dataclasses import FrozenInstanceError
from typing import Annotated

import pytest

from func_to_web import (
    OpenForm,
    ReturnContractError,
    WebFunction,
    WebFunctions,
    router_of,
)
from func_to_web.models.functions import (
    DEFAULT_TITLE,
    functions_of,
    space_of,
)
from func_to_web.templates.index import index_of


def add(a: int, b: int = 2) -> int:
    """Add two numbers."""
    return a + b


def subtract(a: int, b: int = 2) -> int:
    """Subtract two numbers."""
    return a - b


def multiply(a: int, b: int = 2) -> int:
    """Multiply two numbers."""
    return a * b


def divide(a: int, b: int = 2) -> float:
    """Divide two numbers."""
    return a / b


def open_add(a: int = 1) -> Annotated[dict, OpenForm(add)]:
    """Opens the add form."""
    return {"a": a}


def open_missing(a: int = 1) -> Annotated[dict, OpenForm(subtract)]:
    return {"a": a}


def open_hidden(a: int = 1) -> Annotated[dict, OpenForm(add, hidden=("nope",))]:
    return {"a": a}


def slugs_of(space):
    return [web_function.slug for web_function in space.functions]


def listed_slugs(document):
    body = document.split("Functions:\n", 1)[1].split("\n\n", 1)[0]
    return [line.split()[0].removeprefix("/") for line in body.splitlines()]


def block_slugs(document):
    return re.findall(r"^--- /(\S+) ---$", document, flags=re.MULTILINE)


def index_slugs(html):
    return re.findall(r'data-slug="([^"]+)"', html)


def page_routes(space):
    return [
        route.path.removesuffix("/")
        for route in router_of(space).routes
        if route.path.endswith("/")
    ]


def test_a_single_callable_builds_a_space():
    space = functions_of([add])

    assert slugs_of(space) == ["add"]


def test_several_callables_build_a_space():
    space = functions_of([add, subtract, multiply])

    assert slugs_of(space) == ["add", "subtract", "multiply"]


def test_a_prepared_web_function_is_reused():
    prepared = WebFunction(add, slug="sum-two")

    space = functions_of([prepared])

    assert space.functions[0] is prepared


def test_callables_and_web_functions_can_be_mixed():
    space = functions_of([add, WebFunction(subtract, slug="minus")])

    assert slugs_of(space) == ["add", "minus"]


def test_a_generator_is_accepted():
    space = functions_of(item for item in (add, subtract))

    assert slugs_of(space) == ["add", "subtract"]


def test_a_tuple_is_accepted():
    space = functions_of((add, subtract))

    assert slugs_of(space) == ["add", "subtract"]


def test_web_functions_takes_a_tuple_of_web_functions():
    space = WebFunctions((WebFunction(add), WebFunction(subtract)))

    assert slugs_of(space) == ["add", "subtract"]


def test_the_default_title_is_func_to_web():
    assert functions_of([add]).title == "FuncToWeb"
    assert DEFAULT_TITLE == "FuncToWeb"


def test_an_explicit_title_is_kept():
    assert functions_of([add], title="Internal tools").title == (
        "Internal tools"
    )


def test_the_title_is_stored_stripped():
    assert functions_of([add], title="  Internal tools  ").title == (
        "Internal tools"
    )


def test_the_document_is_generated_once_and_names_the_space():
    space = functions_of([add], title="Internal tools")

    assert space.document.startswith("=== Internal tools ===")
    assert "--- /add ---" in space.document


def test_the_document_lists_the_first_line_of_each_description():
    space = functions_of([add, subtract])

    assert "  /add       Add two numbers." in space.document
    assert "  /subtract  Subtract two numbers." in space.document


def test_a_space_without_open_form_has_no_forms():
    assert functions_of([add, subtract]).forms == {}


def test_an_open_form_target_is_resolved_by_callable():
    space = functions_of([open_add, add])

    action = space.forms["open_add"]

    assert action.target is space.functions[1]
    assert action.hidden == ()


def test_an_open_form_target_is_resolved_by_web_function():
    target = WebFunction(add, slug="sum-two")

    def open_target(a: int = 1) -> Annotated[dict, OpenForm(target)]:
        return {"a": a}

    space = functions_of([WebFunction(open_target), target])

    assert space.forms["open_target"].target is target


def test_hidden_names_travel_to_the_resolved_form():
    def open_with_hidden(a: int = 1) -> Annotated[dict, OpenForm(add, ("b",))]:
        return {"a": a}

    space = functions_of([open_with_hidden, add])

    assert space.forms["open_with_hidden"].hidden == ("b",)


@pytest.mark.parametrize(
    "field_name",
    ["functions", "title", "document", "forms"],
)
def test_every_field_is_frozen(field_name):
    space = functions_of([add])

    with pytest.raises(FrozenInstanceError):
        setattr(space, field_name, None)


def test_space_of_wraps_a_bare_callable():
    space = space_of(add, None)

    assert slugs_of(space) == ["add"]
    assert space.title == "FuncToWeb"


def test_space_of_wraps_a_web_function():
    prepared = WebFunction(add)

    space = space_of(prepared, "Tools")

    assert space.functions[0] is prepared
    assert space.title == "Tools"


def test_space_of_wraps_an_iterable():
    space = space_of([add, subtract], "Tools")

    assert slugs_of(space) == ["add", "subtract"]
    assert space.title == "Tools"


def test_space_of_returns_a_prepared_space_untouched():
    prepared = functions_of([add], title="Tools")

    assert space_of(prepared, None) is prepared


def test_an_empty_iterable_is_rejected():
    with pytest.raises(ValueError, match="^at least one function is required$"):
        functions_of([])


def test_an_empty_tuple_is_rejected():
    with pytest.raises(ValueError, match="^at least one function is required$"):
        WebFunctions(())


def test_a_non_iterable_is_rejected():
    with pytest.raises(
        TypeError,
        match="^entries must be callables or WebFunction instances$",
    ):
        space_of(42, None)


def test_a_bare_str_is_rejected():
    with pytest.raises(
        TypeError,
        match="^entries must be callables or WebFunction instances$",
    ):
        space_of("add", None)


def test_bare_bytes_are_rejected():
    with pytest.raises(
        TypeError,
        match="^entries must be callables or WebFunction instances$",
    ):
        space_of(b"add", None)


@pytest.mark.parametrize("value", ["add", 42, None, object()])
def test_an_invalid_entry_is_rejected(value):
    with pytest.raises(
        TypeError,
        match="^entries must be callables or WebFunction instances$",
    ):
        functions_of([value])


@pytest.mark.parametrize("value", [[WebFunction(add)], (item for item in ())])
def test_web_functions_rejects_anything_but_a_tuple(value):
    with pytest.raises(TypeError, match="^functions must be tuple$"):
        WebFunctions(value)


def test_web_functions_rejects_a_raw_callable():
    with pytest.raises(
        TypeError,
        match="^functions must contain only WebFunction instances$",
    ):
        WebFunctions((add,))


def test_the_title_must_be_str():
    with pytest.raises(TypeError, match="^title must be str$"):
        functions_of([add], title=42)


@pytest.mark.parametrize("value", ["", "   ", "\t"])
def test_the_title_cannot_be_empty(value):
    with pytest.raises(ValueError, match="^title cannot be empty$"):
        functions_of([add], title=value)


def test_two_functions_cannot_share_a_slug():
    with pytest.raises(
        ValueError,
        match=re.escape("two functions share the slug 'add'"),
    ):
        functions_of([add, add])


def test_repeating_the_same_web_function_shares_a_slug():
    prepared = WebFunction(add)

    with pytest.raises(
        ValueError,
        match=re.escape("two functions share the slug 'add'"),
    ):
        WebFunctions((prepared, prepared))


def test_the_same_callable_can_be_registered_under_two_slugs():
    space = functions_of(
        [WebFunction(add, slug="sum-two"), WebFunction(add, slug="plus")]
    )

    assert slugs_of(space) == ["sum-two", "plus"]
    assert space.functions[0].fn is space.functions[1].fn


def test_a_prepared_space_refuses_a_new_title():
    prepared = functions_of([add], title="Tools")

    with pytest.raises(
        TypeError,
        match=re.escape(
            "the prepared space already carries its title; "
            "set the title when creating WebFunctions"
        ),
    ):
        space_of(prepared, "Other")


def test_an_unregistered_open_form_target_is_rejected():
    with pytest.raises(
        ReturnContractError,
        match="^OpenForm target is not registered in this space$",
    ):
        functions_of([open_missing])


def test_an_ambiguous_open_form_target_is_rejected():
    with pytest.raises(
        ReturnContractError,
        match="^OpenForm target matches more than one registered function$",
    ):
        WebFunctions(
            (
                WebFunction(open_add),
                WebFunction(add, slug="sum-two"),
                WebFunction(add, slug="plus"),
            )
        )


def test_an_unknown_hidden_field_is_rejected():
    with pytest.raises(
        ReturnContractError,
        match=re.escape("unknown hidden field 'nope' for OpenForm target 'add'"),
    ):
        functions_of([open_hidden, add])


def test_the_declared_order_is_kept_everywhere():
    space = functions_of([multiply, add, divide, subtract], title="Tools")
    expected = ["multiply", "add", "divide", "subtract"]

    assert slugs_of(space) == expected
    assert listed_slugs(space.document) == expected
    assert block_slugs(space.document) == expected
    assert index_slugs(index_of(space, "")) == expected
    assert page_routes(space) == [f"/{slug}" for slug in expected]


def test_the_document_served_is_the_prepared_one(client_factory):
    space = functions_of([multiply, add, divide], title="Tools")
    client = client_factory(space)

    response = client.get("/doc")

    assert response.status_code == 200
    assert response.text == space.document


def test_the_same_space_can_be_mounted_twice(app_factory):
    from fastapi.testclient import TestClient

    space = functions_of([add, subtract], title="Tools")

    first = app_factory(space, prefix="/a")
    second = app_factory(space, prefix="/b")

    with TestClient(first) as client_a, TestClient(second) as client_b:
        assert client_a.get("/a/add/").status_code == 200
        assert client_b.get("/b/add/").status_code == 200

    assert slugs_of(space) == ["add", "subtract"]
