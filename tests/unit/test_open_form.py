import json
from dataclasses import FrozenInstanceError, dataclass
from datetime import date, time
from pathlib import Path
from typing import Annotated
from urllib.parse import parse_qs, unquote, urljoin, urlsplit

import pytest

from shared import Address, Attachment, Priority, TxtFile, carries
from func_to_web import (
    IsPathFile,
    OpenForm,
    ReturnContractError,
    WebFunction,
    WebFunctions,
    router_of,
)

BoundedFile = Annotated[
    str,
    IsPathFile(extensions=(".txt",), min_size=2, max_size=16),
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
        router_of([select_product])

    assert str(error.value) == (
        "OpenForm target is not registered in this space")


def test_an_ambiguous_target_is_a_return_contract_error():
    with pytest.raises(ReturnContractError) as error:
        router_of([WebFunction(edit_product, slug="edit-a"),
                   WebFunction(edit_product, slug="edit-b"),
                   emit_to_callable])

    assert str(error.value) == (
        "OpenForm target matches more than one registered function")


def test_a_web_function_target_resolves_by_identity():
    space = WebFunctions((WebFunction(emit_to_instance), EDIT_INSTANCE))

    assert space.forms["emit_to_instance"].target is EDIT_INSTANCE


def test_an_equivalent_web_function_is_not_the_target():
    with pytest.raises(ReturnContractError) as error:
        router_of([emit_to_instance, WebFunction(edit_product, slug="edit")])

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
        router_of([emit_to_unknown_hidden, edit_product])

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
