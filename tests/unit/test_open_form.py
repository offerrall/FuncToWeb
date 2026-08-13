import json
from dataclasses import FrozenInstanceError, dataclass
from datetime import date, time
from pathlib import Path
from typing import Annotated
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

import pytest

from shared import Address, Attachment, Priority, TxtFile, carries
from func_to_web import (
    FileHint,
    OpenForm,
    ReturnContractError,
    WebFunction,
    WebFunctions,
    app_of,
)

BoundedFile = Annotated[
    str,
    FileHint(extensions=(".txt",), min_size=2, max_size=16),
]


@dataclass
class Product:
    product_id: int
    name: str
    stock: int


@dataclass
class Trip:
    origin: Address
    label: str = "trip"


def edit_product(product_id: int, name: str = "n", stock: int = 0) -> str:
    return "updated"


EDIT_INSTANCE = WebFunction(edit_product, slug="edit")


def store_task(
    task_id: int,
    title: str = "t",
    ratio: float = 0.0,
    done: bool = False,
    priority: Priority = Priority.LOW,
    due: date = date(2026, 8, 1),
    at: time = time(9, 30),
) -> str:
    return "ok"


def describe(document: TxtFile, note: str = "n") -> str:
    return "ok"


def describe_bounded(document: BoundedFile) -> str:
    return "ok"


def describe_many(documents: list[TxtFile], rows: list[Attachment]) -> str:
    return "ok"


def plan_trip(trip: Trip) -> str:
    return "ok"


def select_product(product_id: int = 1) -> Annotated[
    Product,
    OpenForm(edit_product, hidden=("product_id",)),
]:
    return Product(product_id, "Widget", 5)


def select_product_as_dict(product_id: int = 1) -> Annotated[
    dict,
    OpenForm(edit_product),
]:
    return {"product_id": product_id, "name": "Widget"}


def collect_task() -> Annotated[dict, OpenForm(store_task)]:
    return {
        "task_id": 7,
        "title": "hola",
        "ratio": 1.5,
        "done": True,
        "priority": Priority.HIGH,
        "due": date(2026, 8, 1),
        "at": time(9, 30),
    }


def pick(document: TxtFile) -> Annotated[dict, OpenForm(describe)]:
    return {"document": document}


def pick_hidden(document: TxtFile) -> Annotated[
    dict,
    OpenForm(describe, hidden=("document",)),
]:
    return {"document": document}


def pick_elsewhere(document: TxtFile) -> Annotated[dict, OpenForm(describe)]:
    loose = Path(document).parent.parent / "loose.txt"
    loose.write_bytes(Path(document).read_bytes())
    return {"document": str(loose)}


def pick_bounded(document: BoundedFile) -> Annotated[
    dict,
    OpenForm(describe_bounded),
]:
    return {"document": document}


def pick_many(documents: list[TxtFile], rows: list[Attachment]) -> Annotated[
    dict,
    OpenForm(describe_many),
]:
    return {"documents": documents, "rows": rows}


def choose_trip() -> Annotated[dict, OpenForm(plan_trip)]:
    return {"trip": Trip(Address("Gran Via", "Bilbao"))}


def emit_to_callable() -> Annotated[dict, OpenForm(edit_product)]:
    return {"product_id": 1}


def emit_to_instance() -> Annotated[dict, OpenForm(EDIT_INSTANCE)]:
    return {"product_id": 1}


def emit_to_unknown_hidden() -> Annotated[
    dict,
    OpenForm(edit_product, hidden=("nope",)),
]:
    return {"product_id": 1}


def emit_unknown_field() -> Annotated[dict, OpenForm(edit_product)]:
    return {"nope": 1}


def emit_wrong_type() -> Annotated[dict, OpenForm(edit_product)]:
    return {"product_id": "dos"}


def emit_text() -> Annotated[str, OpenForm(edit_product)]:
    return "plain"


def href_of(response):
    return response.json()["result"]["href"]


def leaks(response, path):
    """Whether a local path reaches the client through this response.

    The href percent-encodes its query and the prefill inside it is JSON, so
    the path has to be looked for through both layers, in every rendering it
    takes."""
    return carries(unquote(response.text), path)


def query_of(href):
    return {key: json.loads(value[0])
            for key, value in parse_qs(urlsplit(href).query).items()}


def destination(client, page, href):
    return client.get(urljoin(f"http://testserver{page}", href))


def hidden_of(html):
    start = html.index('id="functoweb-hidden"')
    opening = html.index(">", start) + 1
    return json.loads(html[opening:html.index("</script>", opening)])


def test_open_form_takes_a_callable_target():
    mark = OpenForm(edit_product)

    assert mark.target is edit_product


def test_open_form_takes_a_web_function_target():
    mark = OpenForm(EDIT_INSTANCE)

    assert mark.target is EDIT_INSTANCE


def test_open_form_hides_nothing_by_default():
    assert OpenForm(edit_product).hidden == ()


def test_open_form_keeps_the_hidden_names_it_is_given():
    mark = OpenForm(edit_product, hidden=("product_id", "stock"))

    assert mark.hidden == ("product_id", "stock")


def test_open_form_is_frozen():
    mark = OpenForm(edit_product)

    with pytest.raises(FrozenInstanceError):
        mark.hidden = ("product_id",)


@pytest.mark.parametrize("target, name", [("edit", "str"), (None, "NoneType"),
                                          (3, "int")])
def test_open_form_rejects_an_invalid_target(target, name):
    with pytest.raises(TypeError) as error:
        OpenForm(target)

    assert str(error.value) == (
        f"OpenForm.target must be a function or a WebFunction, got {name}")


def test_open_form_rejects_a_hidden_that_is_not_a_tuple():
    with pytest.raises(TypeError) as error:
        OpenForm(edit_product, hidden=["product_id"])

    assert str(error.value) == "OpenForm.hidden must be a tuple, got list"


def test_open_form_rejects_non_str_hidden_elements():
    with pytest.raises(TypeError) as error:
        OpenForm(edit_product, hidden=(1,))

    assert str(error.value) == "OpenForm.hidden must contain only str"


def test_a_registered_callable_target_resolves_to_its_entry():
    space = WebFunctions((WebFunction(select_product),
                          WebFunction(edit_product)))

    action = space.forms["select_product"]

    assert action.target.fn is edit_product
    assert action.hidden == ("product_id",)


def test_an_unregistered_target_is_a_return_contract_error():
    with pytest.raises(ReturnContractError) as error:
        app_of([select_product])

    assert str(error.value) == (
        "OpenForm target is not registered in this space")


def test_an_ambiguous_target_is_a_return_contract_error():
    with pytest.raises(ReturnContractError) as error:
        app_of([WebFunction(edit_product, slug="edit-a"),
                   WebFunction(edit_product, slug="edit-b"),
                   emit_to_callable])

    assert str(error.value) == (
        "OpenForm target matches more than one registered function")


def test_a_web_function_target_resolves_by_identity():
    space = WebFunctions((WebFunction(emit_to_instance), EDIT_INSTANCE))

    assert space.forms["emit_to_instance"].target is EDIT_INSTANCE


def test_an_equivalent_web_function_is_not_the_target():
    with pytest.raises(ReturnContractError) as error:
        app_of([emit_to_instance, WebFunction(edit_product, slug="edit")])

    assert str(error.value) == (
        "OpenForm target is not registered in this space")


def test_a_web_function_target_wins_over_a_twin_of_its_callable():
    space = WebFunctions((WebFunction(emit_to_instance), EDIT_INSTANCE,
                          WebFunction(edit_product, slug="twin")))

    assert space.forms["emit_to_instance"].target is EDIT_INSTANCE


def test_an_existing_hidden_name_is_accepted():
    space = WebFunctions((WebFunction(select_product),
                          WebFunction(edit_product)))

    assert space.forms["select_product"].hidden == ("product_id",)


def test_an_unknown_hidden_name_is_a_return_contract_error():
    with pytest.raises(ReturnContractError) as error:
        app_of([emit_to_unknown_hidden, edit_product])

    assert str(error.value) == (
        "unknown hidden field 'nope' for OpenForm target 'edit_product'")


def test_a_target_with_a_custom_slug_opens_under_that_slug(client_factory):
    client = client_factory([emit_to_instance, EDIT_INSTANCE])

    response = client.post("/emit_to_instance/invoke", json={})

    assert href_of(response).startswith("../edit/?")


def test_a_dataclass_return_becomes_the_prefill(client_factory):
    client = client_factory([select_product, edit_product])

    response = client.post("/select_product/invoke", json={"product_id": 3})

    assert query_of(href_of(response))["prefill"] == {
        "product_id": 3, "name": "Widget", "stock": 5}


def test_a_dict_return_becomes_the_prefill(client_factory):
    client = client_factory([select_product_as_dict, edit_product])

    response = client.post("/select_product_as_dict/invoke",
                           json={"product_id": 4})

    assert query_of(href_of(response))["prefill"] == {
        "product_id": 4, "name": "Widget"}


def test_scalar_fields_travel_in_their_browser_transport(client_factory):
    client = client_factory([collect_task, store_task])

    response = client.post("/collect_task/invoke", json={})

    assert query_of(href_of(response))["prefill"] == {
        "task_id": 7,
        "title": "hola",
        "ratio": 1.5,
        "done": True,
        "priority": "HIGH",
        "due": "2026-08-01",
        "at": "09:30:00",
    }


def test_a_file_travels_as_its_bare_reference(client_factory, stored_file,
                                              uploads_dir):
    stored_file("a.txt")
    client = client_factory([pick, describe])

    response = client.post("/pick/invoke", json={"document": "a.txt"})
    href = href_of(response)

    assert query_of(href)["prefill"] == {"document": "a.txt"}
    assert not leaks(response, uploads_dir)


def test_a_chained_file_opens_the_destination(client_factory, stored_file):
    stored_file("a.txt")
    client = client_factory([pick, describe])
    response = client.post("/pick/invoke", json={"document": "a.txt"})

    page = destination(client, "/pick/", href_of(response))

    assert page.status_code == 200


def test_a_hidden_file_completes_the_chain_without_a_second_upload(
        client_factory, stored_file, uploads_dir, plan_of_page):
    """A file picked for A reaches B as a reference, and B runs on it.

    The whole point of a hidden file field: the visitor never sees it, never
    picks it again, and the page it lands on carries the name storage knows
    the file by, never the path the server resolved it to.
    """
    stored_file("a.txt", data=b"payload")
    client = client_factory([pick_hidden, describe])
    before = sorted(entry.name for entry in uploads_dir.iterdir())

    opened = client.post("/pick_hidden/invoke", json={"document": "a.txt"})
    href = href_of(opened)
    page = destination(client, "/pick_hidden/", href)
    served = {field["name"]: field.get("default")
              for field in plan_of_page(page.text)["fields"]}

    assert query_of(href)["prefill"] == {"document": "a.txt"}
    assert query_of(href)["hidden"] == ["document"]
    assert page.status_code == 200
    assert served["document"] == "a.txt"
    assert hidden_of(page.text) == ["document"]
    assert not leaks(opened, uploads_dir)
    assert not carries(page.text, uploads_dir)

    ran = client.post("/describe/invoke",
                      json={"document": served["document"], "note": "n"})

    assert ran.status_code == 200
    assert sorted(entry.name for entry in uploads_dir.iterdir()) == before


def test_a_file_with_bounds_travels_and_opens(client_factory, stored_file,
                                              uploads_dir):
    stored_file("a.txt", size=4)
    client = client_factory([pick_bounded, describe_bounded])

    response = client.post("/pick_bounded/invoke", json={"document": "a.txt"})

    assert query_of(href_of(response))["prefill"] == {"document": "a.txt"}
    assert destination(client, "/pick_bounded/",
                       href_of(response)).status_code == 200


def test_a_file_written_outside_the_storage_fails_the_execution(
        client_factory, stored_file, uploads_dir):
    stored_file("a.txt")
    client = client_factory([pick_elsewhere, describe])

    response = client.post("/pick_elsewhere/invoke", json={"document": "a.txt"})

    assert response.status_code == 500
    assert response.json()["error"] == (
        "ReturnContractError: OpenForm returned a file outside the storage "
        "directory: 'loose.txt'")
    assert not leaks(response, uploads_dir.parent)


def test_lists_travel_item_by_item(client_factory, stored_file, uploads_dir):
    stored_file("a.txt")
    stored_file("b.txt")
    client = client_factory([pick_many, describe_many])

    response = client.post("/pick_many/invoke", json={
        "documents": ["a.txt", "b.txt"],
        "rows": [{"document": "a.txt", "tag": "z"}],
    })
    href = href_of(response)

    assert query_of(href)["prefill"] == {
        "documents": ["a.txt", "b.txt"],
        "rows": [{"document": "a.txt", "tag": "z"}],
    }
    assert not leaks(response, uploads_dir)
    assert destination(client, "/pick_many/", href).status_code == 200


def test_a_nested_dataclass_travels_as_a_nested_object(client_factory):
    client = client_factory([choose_trip, plan_trip])

    response = client.post("/choose_trip/invoke", json={})

    assert query_of(href_of(response))["prefill"] == {
        "trip": {"origin": {"street": "Gran Via", "city": "Bilbao"},
                 "label": "trip"}}


def test_an_unknown_returned_field_fails_the_execution(client_factory):
    client = client_factory([emit_unknown_field, edit_product])

    response = client.post("/emit_unknown_field/invoke", json={})

    assert response.status_code == 500
    assert response.json()["error"] == (
        "ReturnContractError: OpenForm returned invalid prefill: "
        "unknown prefill field: 'nope'")


def test_a_returned_field_of_the_wrong_type_fails_the_execution(
        client_factory):
    client = client_factory([emit_wrong_type, edit_product])

    response = client.post("/emit_wrong_type/invoke", json={})

    assert response.status_code == 500
    assert response.json()["error"] == (
        "ReturnContractError: OpenForm returned invalid prefill: "
        "product_id: default: expected int, got str")


def test_a_return_that_is_not_a_mapping_or_dataclass_fails_the_execution(
        client_factory):
    client = client_factory([emit_text, edit_product])

    response = client.post("/emit_text/invoke", json={})

    assert response.status_code == 500
    assert response.json()["error"] == (
        "ReturnContractError: OpenForm return must be a mapping or dataclass "
        "instance")


def test_the_result_is_a_form_output_with_a_relative_href(client_factory):
    client = client_factory([select_product, edit_product])

    response = client.post("/select_product/invoke", json={"product_id": 3})

    assert response.json()["result"]["type"] == "form"
    assert href_of(response).startswith("../edit_product/?")


def test_the_href_stays_relative_under_a_prefix(client_factory):
    client = client_factory([select_product, edit_product], prefix="/tools")

    response = client.post("/tools/select_product/invoke",
                           json={"product_id": 3})

    assert href_of(response).startswith("../edit_product/?")


def test_hidden_is_serialized_in_the_query(client_factory):
    client = client_factory([select_product, edit_product])

    response = client.post("/select_product/invoke", json={"product_id": 3})

    assert query_of(href_of(response))["hidden"] == ["product_id"]


def test_no_hidden_names_leave_the_query_without_hidden(client_factory):
    client = client_factory([select_product_as_dict, edit_product])

    response = client.post("/select_product_as_dict/invoke",
                           json={"product_id": 4})

    assert "hidden" not in query_of(href_of(response))


def test_the_destination_page_really_opens(client_factory):
    client = client_factory([select_product, edit_product])
    response = client.post("/select_product/invoke", json={"product_id": 3})

    page = destination(client, "/select_product/", href_of(response))

    assert page.status_code == 200


def test_the_destination_page_opens_under_a_prefix(client_factory):
    client = client_factory([select_product, edit_product], prefix="/tools")
    response = client.post("/tools/select_product/invoke",
                           json={"product_id": 3})

    page = destination(client, "/tools/select_product/", href_of(response))

    assert page.status_code == 200


def test_the_destination_page_keeps_the_space_theme(client_factory,
                                                    html_root):
    client = client_factory([select_product, edit_product], theme="dark")
    response = client.post("/select_product/invoke", json={"product_id": 3})

    page = destination(client, "/select_product/", href_of(response))

    assert 'data-pth-theme="dark"' in html_root(page.text)


def test_the_destination_page_carries_the_prefill_and_the_hidden_names(
        client_factory, plan_of_page):
    client = client_factory([select_product, edit_product])
    response = client.post("/select_product/invoke", json={"product_id": 3})

    page = destination(client, "/select_product/", href_of(response))
    plan = plan_of_page(page.text)

    assert {field["name"]: field.get("default") for field in plan["fields"]} == {
        "product_id": 3, "name": "Widget", "stock": 5}
    assert hidden_of(page.text) == ["product_id"]


def test_the_opening_also_arrives_over_the_stream(client_factory, sse):
    client = client_factory([select_product, edit_product])

    response = client.post("/select_product/invoke-stream",
                           json={"product_id": 3})
    events = sse(response.text)

    assert [name for name, _ in events] == ["start", "result"]
    assert events[-1][1]["result"]["type"] == "form"


# ---------------------------------------------------------------------------
# Unions
# ---------------------------------------------------------------------------
#
# A plan writes a union default as {"branch": index, "value": ...}, and that is
# the plan's grammar rather than the transport: the destination reads a prefill
# the way it reads a submit. Before 2.6.0 the opening published the plan form
# as if it were transport, and every union of two or more branches answered
# 400 — "expected int | str, got dict" for a plain one, "wrap it as $type" for
# an ambiguous one. What is pinned here is the browser's contract, one case per
# mode, in both directions: what leaves in the query, and what the destination
# builds from it.


@dataclass
class Note:
    text: str = "n"


@dataclass
class Memo:
    body: str = "m"


@dataclass
class Cell:
    content: int | str = 0


def told(value):
    """A value with the type it arrived as, so a branch cannot be mistaken.

    A list spells out its items: list[str] and list[int] are one JSON array,
    and telling them apart is the whole of what these tests are about.
    """
    if type(value) is list:
        return "[" + "|".join(told(item) for item in value) + "]"

    return f"{type(value).__name__}:{value!r}"


def take_mix(mix: int | str) -> str:
    """int and str never collide on the wire, so both branches travel plain."""
    return told(mix)


def take_items(items: list[str] | list[int]) -> str:
    """One JSON array for both branches: the wrapped mode."""
    return told(items)


def take_when(when: date | str) -> str:
    """A date travels as text, so it collides with str and is wrapped."""
    return told(when)


def take_level(level: Priority | str) -> str:
    """An enum travels as its name, which is text, so it is wrapped too."""
    return told(level)


def take_row(row: Note | Memo) -> str:
    """Dataclasses share the dict and name themselves inline."""
    return told(row)


def take_pick(pick: int | date | Priority) -> str:
    """Three branches, mixed modes: one plain, two sharing the string."""
    return told(pick)


def take_cell(cell: Cell) -> str:
    """A union reached through a dataclass field."""
    return told(cell.content)


def take_cells(cells: list[int | str]) -> str:
    """A plain union reached through a list item."""
    return told(cells)


def take_moments(moments: list[date | str]) -> str:
    """A wrapped union reached through a list item."""
    return told(moments)


def take_maybe(maybe: int | None) -> str:
    """One real branch, so plan_of() compiles no choice at all."""
    return told(maybe)


def take_branch_files(items: list[TxtFile] | list[int]) -> str:
    """A file reference inside a wrapped branch."""
    return told([Path(item).name if type(item) is str else item
                 for item in items])


def open_mix_int() -> Annotated[dict, OpenForm(take_mix)]:
    return {"mix": 7}


def open_mix_str() -> Annotated[dict, OpenForm(take_mix)]:
    return {"mix": "seven"}


def open_mix_hidden() -> Annotated[
    dict,
    OpenForm(take_mix, hidden=("mix",)),
]:
    return {"mix": 7}


def open_items_str() -> Annotated[dict, OpenForm(take_items)]:
    return {"items": ["a", "b"]}


def open_items_int() -> Annotated[dict, OpenForm(take_items)]:
    return {"items": [1, 2]}


def open_when_date() -> Annotated[dict, OpenForm(take_when)]:
    return {"when": date(2026, 8, 1)}


def open_when_str() -> Annotated[dict, OpenForm(take_when)]:
    return {"when": "soon"}


def open_level_enum() -> Annotated[dict, OpenForm(take_level)]:
    return {"level": Priority.HIGH}


def open_level_str() -> Annotated[dict, OpenForm(take_level)]:
    return {"level": "urgent"}


def open_row_note() -> Annotated[dict, OpenForm(take_row)]:
    return {"row": Note("hola")}


def open_row_memo() -> Annotated[dict, OpenForm(take_row)]:
    return {"row": Memo("adios")}


def open_pick_first() -> Annotated[dict, OpenForm(take_pick)]:
    return {"pick": 3}


def open_pick_second() -> Annotated[dict, OpenForm(take_pick)]:
    return {"pick": date(2026, 8, 1)}


def open_pick_third() -> Annotated[dict, OpenForm(take_pick)]:
    return {"pick": Priority.LOW}


def open_cell() -> Annotated[dict, OpenForm(take_cell)]:
    return {"cell": Cell("inner")}


def open_cells() -> Annotated[dict, OpenForm(take_cells)]:
    return {"cells": [1, "a"]}


def open_moments() -> Annotated[dict, OpenForm(take_moments)]:
    return {"moments": [date(2026, 8, 1), "soon"]}


def open_maybe() -> Annotated[dict, OpenForm(take_maybe)]:
    return {"maybe": 5}


def open_maybe_none() -> Annotated[dict, OpenForm(take_maybe)]:
    return {"maybe": None}


def pick_branch_files(documents: list[TxtFile]) -> Annotated[
    dict,
    OpenForm(take_branch_files),
]:
    return {"items": documents}


# (opener, target, what the query carries, what the destination's own plan
# publishes back, what the destination builds). The fourth column is the plan
# grammar and the third is the transport: keeping both in one row is what
# states that they differ and that the branch is the same in each.
UNIONS = [
    (open_mix_int, take_mix,
     {"mix": 7},
     {"mix": {"branch": 0, "value": 7}},
     "int:7"),
    (open_mix_str, take_mix,
     {"mix": "seven"},
     {"mix": {"branch": 1, "value": "seven"}},
     "str:'seven'"),
    (open_items_str, take_items,
     {"items": {"$type": "list[str]", "$value": ["a", "b"]}},
     {"items": {"branch": 0, "value": ["a", "b"]}},
     "[str:'a'|str:'b']"),
    (open_items_int, take_items,
     {"items": {"$type": "list[int]", "$value": [1, 2]}},
     {"items": {"branch": 1, "value": [1, 2]}},
     "[int:1|int:2]"),
    (open_when_date, take_when,
     {"when": {"$type": "date", "$value": "2026-08-01"}},
     {"when": {"branch": 0, "value": "2026-08-01"}},
     "date:datetime.date(2026, 8, 1)"),
    (open_when_str, take_when,
     {"when": {"$type": "str", "$value": "soon"}},
     {"when": {"branch": 1, "value": "soon"}},
     "str:'soon'"),
    (open_level_enum, take_level,
     {"level": {"$type": "Priority", "$value": "HIGH"}},
     {"level": {"branch": 0, "value": "HIGH"}},
     "Priority:<Priority.HIGH: 'high'>"),
    (open_level_str, take_level,
     {"level": {"$type": "str", "$value": "urgent"}},
     {"level": {"branch": 1, "value": "urgent"}},
     "str:'urgent'"),
    (open_row_note, take_row,
     {"row": {"$type": "Note", "text": "hola"}},
     {"row": {"branch": 0, "value": {"text": "hola"}}},
     "Note:Note(text='hola')"),
    (open_row_memo, take_row,
     {"row": {"$type": "Memo", "body": "adios"}},
     {"row": {"branch": 1, "value": {"body": "adios"}}},
     "Memo:Memo(body='adios')"),
    (open_pick_first, take_pick,
     {"pick": 3},
     {"pick": {"branch": 0, "value": 3}},
     "int:3"),
    (open_pick_second, take_pick,
     {"pick": {"$type": "date", "$value": "2026-08-01"}},
     {"pick": {"branch": 1, "value": "2026-08-01"}},
     "date:datetime.date(2026, 8, 1)"),
    (open_pick_third, take_pick,
     {"pick": {"$type": "Priority", "$value": "LOW"}},
     {"pick": {"branch": 2, "value": "LOW"}},
     "Priority:<Priority.LOW: 'low'>"),
    (open_cell, take_cell,
     {"cell": {"content": "inner"}},
     {"cell": {"content": {"branch": 1, "value": "inner"}}},
     "str:'inner'"),
    (open_cells, take_cells,
     {"cells": [1, "a"]},
     {"cells": [{"branch": 0, "value": 1}, {"branch": 1, "value": "a"}]},
     "[int:1|str:'a']"),
    (open_moments, take_moments,
     {"moments": [{"$type": "date", "$value": "2026-08-01"},
                  {"$type": "str", "$value": "soon"}]},
     {"moments": [{"branch": 0, "value": "2026-08-01"},
                  {"branch": 1, "value": "soon"}]},
     "[date:datetime.date(2026, 8, 1)|str:'soon']"),
    # X | None has a single real branch, so plan_of() compiles no choice node
    # and the two grammars already agree. It is here to stay that way.
    (open_maybe, take_maybe, {"maybe": 5}, {"maybe": 5}, "int:5"),
    (open_maybe_none, take_maybe,
     {"maybe": None}, {"maybe": None}, "NoneType:None"),
]

UNION_IDS = [opener.__name__ for opener, *_ in UNIONS]


def plan_shaped(value):
    """Whether a plan's union representation survives anywhere inside value.

    The barrier the fix exists for. {"branch": ..., "value": ...} is what a
    plan publishes and what no query may carry, at any depth: through a list,
    through a dataclass, or inside another branch.
    """
    if type(value) is dict:
        return (set(value) == {"branch", "value"}
                or any(plan_shaped(item) for item in value.values()))

    if type(value) is list:
        return any(plan_shaped(item) for item in value)

    return False


def opened(client, opener):
    response = client.post(f"/{opener.__name__}/invoke", json={})

    assert response.status_code == 200

    return response


@pytest.mark.parametrize("opener, target, transport, published, built", UNIONS,
                         ids=UNION_IDS)
def test_a_union_default_travels_in_the_transport_a_submit_sends(
        client_factory, opener, target, transport, published, built):
    client = client_factory([opener, target])

    response = opened(client, opener)

    assert query_of(href_of(response))["prefill"] == transport


@pytest.mark.parametrize("opener, target, transport, published, built", UNIONS,
                         ids=UNION_IDS)
def test_a_union_opening_carries_no_plan_representation(
        client_factory, opener, target, transport, published, built):
    client = client_factory([opener, target])

    response = opened(client, opener)

    assert not plan_shaped(query_of(href_of(response))["prefill"])


@pytest.mark.parametrize("opener, target, transport, published, built", UNIONS,
                         ids=UNION_IDS)
def test_the_destination_of_a_union_opening_really_opens(
        client_factory, opener, target, transport, published, built):
    client = client_factory([opener, target])
    response = opened(client, opener)

    page = destination(client, f"/{opener.__name__}/", href_of(response))

    assert page.status_code == 200


@pytest.mark.parametrize("opener, target, transport, published, built", UNIONS,
                         ids=UNION_IDS)
def test_the_destination_page_opens_on_the_branch_the_opener_chose(
        client_factory, plan_of_page, opener, target, transport, published,
        built):
    """Plan, transport, plan again: the branch index comes back the same.

    The page the destination renders publishes a plan of its own, so the mode
    the switcher opens on is readable. This is the round trip the conversion
    has to be faithful across, and the column it compares against is the plan
    grammar the query is no longer allowed to carry.
    """
    client = client_factory([opener, target])
    response = opened(client, opener)

    page = destination(client, f"/{opener.__name__}/", href_of(response))
    served = {field["name"]: field.get("default")
              for field in plan_of_page(page.text)["fields"]}

    assert page.status_code == 200
    assert served == published


@pytest.mark.parametrize("opener, target, transport, published, built", UNIONS,
                         ids=UNION_IDS)
def test_a_union_opening_rebuilds_the_value_it_was_given(
        client_factory, opener, target, transport, published, built):
    """The branch survives the trip, which a status code does not say.

    list[str] and list[int] both parse; what says the right one was chosen is
    the value the destination builds out of the prefill it was handed.
    """
    client = client_factory([opener, target])
    response = opened(client, opener)

    ran = client.post(f"/{target.__name__}/invoke",
                      json=query_of(href_of(response))["prefill"])

    assert ran.status_code == 200
    assert ran.json()["result"]["value"] == built


def test_a_hidden_union_field_travels_and_opens(client_factory):
    client = client_factory([open_mix_hidden, take_mix])

    response = opened(client, open_mix_hidden)
    href = href_of(response)
    page = destination(client, "/open_mix_hidden/", href)

    assert query_of(href)["prefill"] == {"mix": 7}
    assert query_of(href)["hidden"] == ["mix"]
    assert page.status_code == 200
    assert hidden_of(page.text) == ["mix"]


def test_a_file_reference_inside_a_wrapped_branch_travels_and_runs(
        client_factory, stored_file, uploads_dir):
    """The two walks of an opening meet here, and neither may undo the other.

    with_references() rewrites the file default in the plan's grammar and the
    transport conversion runs after it, so the reference has to survive the
    wrapping and the wrapping has to survive the reference.
    """
    stored_file("a.txt")
    client = client_factory([pick_branch_files, take_branch_files])

    response = client.post("/pick_branch_files/invoke",
                           json={"documents": ["a.txt"]})
    href = href_of(response)

    assert query_of(href)["prefill"] == {
        "items": {"$type": "list[str]", "$value": ["a.txt"]}}
    assert not leaks(response, uploads_dir)

    ran = client.post("/take_branch_files/invoke",
                      json=query_of(href)["prefill"])

    assert ran.status_code == 200
    assert ran.json()["result"]["value"] == "[str:'a.txt']"
