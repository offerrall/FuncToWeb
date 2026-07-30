import json
from dataclasses import dataclass
from datetime import date, time
from typing import Annotated

import pytest

from shared import Address, Attachment, Priority, TxtFile, carries
from func_to_web import IsPathFile, Max, Min, WebFunction, page_of
from func_to_web.models.function import build_prefill
from func_to_web.web.upload import stored_file as resolve_reference

BoundedFile = Annotated[
    str,
    IsPathFile(extensions=(".txt",), min_size=4, max_size=8),
]

ABSENT = object()


@dataclass
class Trip:
    origin: Address
    label: str = "trip"


def edit_task(
    task_id: int,
    ratio: float,
    title: Annotated[str, Min(3), Max(20)],
    done: bool,
    priority: Priority,
    due: date,
    at: time,
    note: str | None,
    tags: list[str],
    mix: int | str,
    where: Address,
) -> str:
    return "ok"


def plan_trip(trip: Trip) -> str:
    return "ok"


def read_document(document: TxtFile) -> str:
    return "ok"


def read_bounded(document: BoundedFile) -> str:
    return "ok"


def read_documents(documents: list[TxtFile]) -> str:
    return "ok"


def read_optional_documents(documents: list[TxtFile | None]) -> str:
    return "ok"


def read_mixed_documents(documents: list[TxtFile | int]) -> str:
    return "ok"


def read_grouped_documents(documents: list[list[TxtFile]]) -> str:
    return "ok"


def read_attachments(rows: list[Attachment]) -> str:
    return "ok"


def http_task(
    task_id: int,
    title: Annotated[str, Min(3)] = "abc",
    priority: Priority = Priority.LOW,
    due: date = date(2026, 8, 1),
) -> str:
    return "ok"


def counted(task_id: int) -> str:
    return str(task_id)


COMPLETE = {
    "task_id": 7,
    "ratio": 1.5,
    "title": "hola",
    "done": True,
    "priority": Priority.HIGH,
    "due": date(2026, 8, 1),
    "at": time(9, 30),
    "note": "n",
    "tags": ["a", "b"],
    "mix": "s",
    "where": Address("Gran Via", "Bilbao"),
}


def hidden_of(html):
    start = html.index('id="functoweb-hidden"')
    opening = html.index(">", start) + 1
    closing = html.index("</script>", opening)
    return json.loads(html[opening:closing])


def defaults_of(plan):
    return {field["name"]: field.get("default", ABSENT)
            for field in plan["fields"]}


def opened(fn, prefill, plan_of_page):
    return defaults_of(plan_of_page(page_of(WebFunction(fn), prefill=prefill)))


def resolved(fn, data, resolver=resolve_reference):
    web_function = WebFunction(fn)
    values = build_prefill(web_function.schema, data, file_resolver=resolver)
    return web_function, values


def file_defaults(fn, data, plan_of_page):
    web_function, values = resolved(fn, data)
    return defaults_of(plan_of_page(page_of(web_function, prefill=values)))


def test_empty_prefill_returns_the_base_page():
    web_function = WebFunction(edit_task)

    assert page_of(web_function, prefill={}) is web_function.html


def test_partial_prefill_leaves_the_other_fields_untouched(plan_of_page):
    values = opened(edit_task, {"task_id": 3}, plan_of_page)

    assert values["task_id"] == 3
    assert all(value is ABSENT
               for name, value in values.items() if name != "task_id")


def test_complete_prefill_sets_every_field(plan_of_page):
    values = opened(edit_task, COMPLETE, plan_of_page)

    assert all(value is not ABSENT for value in values.values())


def test_int_prefill_travels_as_a_number(plan_of_page):
    assert opened(edit_task, {"task_id": 7}, plan_of_page)["task_id"] == 7


def test_float_prefill_travels_as_a_number(plan_of_page):
    assert opened(edit_task, {"ratio": 1.5}, plan_of_page)["ratio"] == 1.5


def test_str_prefill_travels_as_text(plan_of_page):
    assert opened(edit_task, {"title": "hola"}, plan_of_page)["title"] == "hola"


def test_bool_prefill_travels_as_a_boolean(plan_of_page):
    assert opened(edit_task, {"done": True}, plan_of_page)["done"] is True


def test_enum_prefill_travels_as_its_member_name(plan_of_page):
    values = opened(edit_task, {"priority": Priority.HIGH}, plan_of_page)

    assert values["priority"] == "HIGH"


def test_date_prefill_travels_as_iso_text(plan_of_page):
    values = opened(edit_task, {"due": date(2026, 8, 1)}, plan_of_page)

    assert values["due"] == "2026-08-01"


def test_time_prefill_travels_as_iso_text(plan_of_page):
    values = opened(edit_task, {"at": time(9, 30)}, plan_of_page)

    assert values["at"] == "09:30:00"


def test_optional_prefill_sets_the_value(plan_of_page):
    assert opened(edit_task, {"note": "n"}, plan_of_page)["note"] == "n"


def test_list_prefill_sets_every_item(plan_of_page):
    values = opened(edit_task, {"tags": ["a", "b"]}, plan_of_page)

    assert values["tags"] == ["a", "b"]


def test_union_prefill_names_its_branch(plan_of_page):
    values = opened(edit_task, {"mix": "s"}, plan_of_page)

    assert values["mix"] == {"branch": 1, "value": "s"}


def test_dataclass_prefill_sets_every_field(plan_of_page):
    values = opened(edit_task, {"where": Address("Gran Via", "Bilbao")},
                    plan_of_page)

    assert values["where"] == {"street": "Gran Via", "city": "Bilbao"}


def test_nested_dataclass_prefill_reaches_the_inner_fields(plan_of_page):
    values = opened(plan_trip, {"trip": Trip(Address("Gran Via", "Bilbao"))},
                    plan_of_page)

    assert values["trip"] == {
        "origin": {"street": "Gran Via", "city": "Bilbao"},
        "label": "trip",
    }


def test_file_prefill_travels_as_its_bare_reference(stored_file,
                                                    plan_of_page):
    stored_file("a.txt")

    values = file_defaults(read_document, {"document": "a.txt"}, plan_of_page)

    assert values["document"] == "a.txt"


def test_list_of_files_prefill_travels_as_bare_references(stored_file,
                                                          plan_of_page):
    stored_file("a.txt")
    stored_file("b.txt")

    values = file_defaults(read_documents, {"documents": ["a.txt", "b.txt"]},
                           plan_of_page)

    assert values["documents"] == ["a.txt", "b.txt"]


def test_list_of_optional_files_prefill_keeps_the_none_item(stored_file,
                                                            plan_of_page):
    stored_file("a.txt")

    values = file_defaults(read_optional_documents,
                           {"documents": ["a.txt", None]}, plan_of_page)

    assert values["documents"] == ["a.txt", None]


def test_list_of_file_or_int_prefill_names_each_branch(stored_file,
                                                       plan_of_page):
    stored_file("a.txt")

    values = file_defaults(read_mixed_documents, {"documents": ["a.txt", 3]},
                           plan_of_page)

    assert values["documents"] == [
        {"branch": 0, "value": "a.txt"},
        {"branch": 1, "value": 3},
    ]


def test_list_of_list_of_files_prefill_keeps_the_grouping(stored_file,
                                                          plan_of_page):
    stored_file("a.txt")
    stored_file("b.txt")

    values = file_defaults(read_grouped_documents,
                           {"documents": [["a.txt"], ["b.txt"]]}, plan_of_page)

    assert values["documents"] == [["a.txt"], ["b.txt"]]


def test_list_of_dataclasses_with_file_prefill_reaches_the_file(
        stored_file, plan_of_page):
    stored_file("a.txt")

    values = file_defaults(read_attachments,
                           {"rows": [{"document": "a.txt", "tag": "z"}]},
                           plan_of_page)

    assert values["rows"] == [{"document": "a.txt", "tag": "z"}]


def test_the_served_page_carries_no_local_path(stored_file, uploads_dir,
                                               plan_of_page):
    stored_file("a.txt")
    web_function, values = resolved(read_attachments,
                                    {"rows": [{"document": "a.txt"}]})

    html = page_of(web_function, prefill=values)

    assert defaults_of(plan_of_page(html))["rows"] == [{"document": "a.txt",
                                                        "tag": "t"}]
    assert not carries(html, uploads_dir)


def test_a_prefilled_file_outside_the_storage_is_refused(sized_file):
    outside = sized_file("loose.txt")

    with pytest.raises(ValueError) as error:
        page_of(WebFunction(read_document), prefill={"document": str(outside)})

    assert str(error.value) == (
        "document: default: file is not in the storage directory: 'loose.txt'")


def test_partial_nested_dataclass_prefill_fills_its_own_defaults(plan_of_page):
    web_function = WebFunction(edit_task)
    values = build_prefill(web_function.schema, {"where": {"street": "Gran Via"}})

    plan = plan_of_page(page_of(web_function, prefill=values))

    assert defaults_of(plan)["where"] == {"street": "Gran Via",
                                          "city": "Madrid"}


def test_unknown_prefill_name_is_a_value_error():
    with pytest.raises(ValueError) as error:
        page_of(WebFunction(edit_task), prefill={"nope": 1})

    assert "unknown prefill field: 'nope'" in str(error.value)


def test_invalid_prefill_type_is_a_type_error():
    with pytest.raises(TypeError) as error:
        page_of(WebFunction(edit_task), prefill={"task_id": "dos"})

    assert "task_id: default: expected int, got str" in str(error.value)


def test_invalid_prefill_value_is_a_value_error():
    with pytest.raises(ValueError) as error:
        page_of(WebFunction(edit_task), prefill={"title": "ab"})

    assert "title: default: too short: 2 chars, minimum 3" in str(error.value)


def test_missing_file_reference_is_a_file_not_found_error():
    with pytest.raises(FileNotFoundError) as error:
        resolved(read_document, {"document": "nope.txt"})

    assert "File not found: nope.txt" in str(error.value)


def test_directory_reference_is_a_file_not_found_error(uploads_dir):
    (uploads_dir / "folder").mkdir()

    with pytest.raises(FileNotFoundError) as error:
        resolved(read_document, {"document": "folder"})

    assert "File not found: folder" in str(error.value)


def test_wrong_extension_is_a_value_error(stored_file):
    stored_file("notes.pdf")

    with pytest.raises(ValueError) as error:
        resolved(read_document, {"document": "notes.pdf"})

    assert "document: not an accepted file type" in str(error.value)


def test_file_below_min_size_is_a_value_error(stored_file):
    stored_file("small.txt", size=1)

    with pytest.raises(ValueError) as error:
        resolved(read_bounded, {"document": "small.txt"})

    assert "document: file too small: 1 bytes, minimum 4" in str(error.value)


def test_file_above_max_size_is_a_value_error(stored_file):
    stored_file("big.txt", size=64)

    with pytest.raises(ValueError) as error:
        resolved(read_bounded, {"document": "big.txt"})

    assert "document: file too large: 64 bytes, maximum 8" in str(error.value)


def test_reference_outside_the_storage_is_a_value_error():
    with pytest.raises(ValueError) as error:
        resolved(read_document, {"document": "../evil.txt"})

    assert ("invalid file reference '../evil.txt': is not a file of the "
            "storage directory") in str(error.value)


def test_absolute_reference_is_a_value_error():
    with pytest.raises(ValueError) as error:
        resolved(read_document, {"document": "/etc/passwd"})

    assert ("invalid file reference '/etc/passwd': is not a file of the "
            "storage directory") in str(error.value)


def test_a_resolver_that_raises_propagates_unchanged():
    def angry(reference):
        raise RuntimeError("resolver exploded")

    with pytest.raises(RuntimeError) as error:
        resolved(read_document, {"document": "a.txt"}, resolver=angry)

    assert "resolver exploded" in str(error.value)


def test_hidden_none_returns_the_base_page():
    web_function = WebFunction(edit_task)

    assert page_of(web_function, hidden=None) is web_function.html


def test_hidden_empty_iterable_returns_the_base_page():
    web_function = WebFunction(edit_task)

    assert page_of(web_function, hidden=[]) is web_function.html


def test_hidden_accepts_a_tuple():
    html = page_of(WebFunction(edit_task), hidden=("task_id",))

    assert hidden_of(html) == ["task_id"]


def test_hidden_accepts_a_list():
    html = page_of(WebFunction(edit_task), hidden=["task_id"])

    assert hidden_of(html) == ["task_id"]


def test_hidden_accepts_a_generator():
    html = page_of(WebFunction(edit_task),
                   hidden=(name for name in ["task_id"]))

    assert hidden_of(html) == ["task_id"]


def test_hidden_one_field_hides_only_that_one():
    html = page_of(WebFunction(edit_task), hidden=["title"])

    assert hidden_of(html) == ["title"]


def test_hidden_several_fields_travel_sorted_and_deduplicated():
    html = page_of(WebFunction(edit_task),
                   hidden=["title", "task_id", "title"])

    assert hidden_of(html) == ["task_id", "title"]


def test_hidden_rejects_a_bare_str():
    with pytest.raises(TypeError) as error:
        page_of(WebFunction(edit_task), hidden="task_id")

    assert "hidden must be an iterable of str, not a single str" in str(
        error.value)


def test_hidden_rejects_non_str_elements():
    with pytest.raises(TypeError) as error:
        page_of(WebFunction(edit_task), hidden=[1])

    assert "hidden must contain only str" in str(error.value)


def test_unknown_hidden_name_hides_nothing_else_and_still_renders(
        plan_of_page):
    web_function = WebFunction(edit_task)

    html = page_of(web_function, hidden=["nope"])

    assert hidden_of(html) == ["nope"]
    assert plan_of_page(html) == web_function.plan


def test_hidden_keeps_the_prefilled_value_in_the_plan(plan_of_page):
    html = page_of(WebFunction(edit_task), prefill={"task_id": 7},
                   hidden=["task_id"])

    assert defaults_of(plan_of_page(html))["task_id"] == 7


def test_hidden_field_ships_no_markup_of_its_own():
    html = page_of(WebFunction(edit_task), hidden=["task_id"])

    assert '<div id="fields"></div>' in html
    assert hidden_of(html) == ["task_id"]


def test_hidden_does_not_skip_validation(client_factory):
    client = client_factory([http_task])
    page = client.get("/http_task/",
                      params={"hidden": json.dumps(["task_id"])})

    response = client.post("/http_task/invoke", json={"title": "abc"})

    assert page.status_code == 200
    assert response.status_code == 422
    assert "missing argument(s): task_id" in response.json()["error"]


def test_hidden_hides_but_does_not_pin_the_prefilled_value(client_factory):
    client = client_factory([counted])
    client.get("/counted/", params={
        "prefill": json.dumps({"task_id": 7}),
        "hidden": json.dumps(["task_id"]),
    })

    response = client.post("/counted/invoke", json={"task_id": 9})

    assert response.json()["result"]["value"] == "9"


def test_hidden_without_prefill_builds_a_fresh_page():
    web_function = WebFunction(edit_task)

    html = page_of(web_function, hidden=["task_id"])

    assert html is not web_function.html
    assert html != web_function.html


def test_applying_a_prefill_does_not_mutate_the_web_function(plan_of_page):
    web_function = WebFunction(edit_task)
    before = json.dumps(web_function.plan, sort_keys=True)
    defaults = [param.default for param in web_function.schema.params]

    page_of(web_function, prefill=COMPLETE, hidden=["task_id"])

    assert json.dumps(web_function.plan, sort_keys=True) == before
    assert [param.default for param in web_function.schema.params] == defaults
    assert plan_of_page(web_function.html) == web_function.plan


def test_page_with_prefill_and_hidden_is_served(client_factory):
    client = client_factory([http_task])

    response = client.get("/http_task/", params={
        "prefill": json.dumps({"task_id": 7}),
        "hidden": json.dumps(["task_id"]),
    })

    assert response.status_code == 200
    assert hidden_of(response.text) == ["task_id"]


def test_prefill_that_is_not_valid_json_is_rejected(client_factory):
    client = client_factory([http_task])

    response = client.get("/http_task/", params={"prefill": "{not json"})

    assert response.status_code == 400
    assert response.json()["detail"] == "prefill must be valid JSON"


def test_prefill_root_that_is_not_an_object_is_rejected(client_factory):
    client = client_factory([http_task])

    response = client.get("/http_task/", params={"prefill": "[1, 2]"})

    assert response.status_code == 400
    assert response.json()["detail"] == "prefill must be a JSON object"


def test_unknown_prefill_field_over_http_is_rejected(client_factory):
    client = client_factory([http_task])

    response = client.get("/http_task/",
                          params={"prefill": json.dumps({"nope": 1})})

    assert response.status_code == 400
    assert response.json()["detail"] == "unknown prefill field: 'nope'"


def test_wrong_prefill_type_over_http_is_rejected(client_factory):
    client = client_factory([http_task])

    response = client.get("/http_task/",
                          params={"prefill": json.dumps({"task_id": "dos"})})

    assert response.status_code == 400
    assert response.json()["detail"] == "task_id: expected int, got str"


def test_prefill_breaking_a_constraint_over_http_is_rejected(client_factory):
    client = client_factory([http_task])

    response = client.get("/http_task/",
                          params={"prefill": json.dumps({"title": "ab"})})

    assert response.status_code == 400
    assert response.json()["detail"] == "title: too short: 2 chars, minimum 3"


def test_unknown_enum_member_over_http_is_rejected(client_factory):
    client = client_factory([http_task])

    response = client.get(
        "/http_task/", params={"prefill": json.dumps({"priority": "URGENT"})})

    assert response.status_code == 400
    assert response.json()["detail"] == "priority: expected Priority, got str"


def test_non_iso_date_over_http_is_rejected(client_factory):
    client = client_factory([http_task])

    response = client.get(
        "/http_task/", params={"prefill": json.dumps({"due": "30/07/2026"})})

    assert response.status_code == 400
    assert response.json()["detail"] == "due: expected date, got str"


def test_hidden_that_is_not_valid_json_is_rejected(client_factory):
    client = client_factory([http_task])

    response = client.get("/http_task/", params={"hidden": "[not json"})

    assert response.status_code == 400
    assert response.json()["detail"] == "hidden must be valid JSON"


def test_hidden_that_is_not_an_array_is_rejected(client_factory):
    client = client_factory([http_task])

    response = client.get("/http_task/",
                          params={"hidden": json.dumps({"a": 1})})

    assert response.status_code == 400
    assert response.json()["detail"] == "hidden must be a JSON array"


def test_hidden_with_non_string_elements_is_rejected(client_factory):
    client = client_factory([http_task])

    response = client.get("/http_task/",
                          params={"hidden": json.dumps(["a", 1])})

    assert response.status_code == 400
    assert response.json()["detail"] == "hidden must contain only strings"


def test_unknown_hidden_name_over_http_is_accepted(client_factory):
    client = client_factory([http_task])

    response = client.get("/http_task/",
                          params={"hidden": json.dumps(["nope"])})

    assert response.status_code == 200
    assert hidden_of(response.text) == ["nope"]


def test_repeated_hidden_name_over_http_hides_once(client_factory):
    client = client_factory([http_task])

    response = client.get(
        "/http_task/", params={"hidden": json.dumps(["task_id", "task_id"])})

    assert response.status_code == 200
    assert hidden_of(response.text) == ["task_id"]


def test_empty_hidden_list_over_http_is_the_base_page(client_factory):
    client = client_factory([http_task])
    base = client.get("/http_task/").text

    response = client.get("/http_task/", params={"hidden": json.dumps([])})

    assert response.status_code == 200
    assert response.text == base


def test_stored_file_prefill_over_http_opens_the_page(client_factory,
                                                      stored_file,
                                                      uploads_dir,
                                                      plan_of_page):
    stored_file("a.txt")
    client = client_factory([read_document])

    response = client.get("/read_document/",
                          params={"prefill": json.dumps({"document": "a.txt"})})

    assert response.status_code == 200
    assert defaults_of(plan_of_page(response.text))["document"] == "a.txt"
    assert not carries(response.text, uploads_dir)


def test_the_prefilled_reference_completes_the_round_trip(client_factory,
                                                          stored_file,
                                                          uploads_dir,
                                                          plan_of_page,
                                                          pending_file):
    pending_file("a.txt", data=b"hello")
    client = client_factory([read_document])

    page = client.get("/read_document/",
                      params={"prefill": json.dumps({"document": "a.txt"})})
    served = defaults_of(plan_of_page(page.text))["document"]
    response = client.post("/read_document/invoke", json={"document": served})

    assert served == "a.txt"
    assert response.status_code == 200
    assert (uploads_dir / "a.txt").read_bytes() == b"hello"


def test_missing_file_prefill_over_http_is_rejected(client_factory):
    client = client_factory([read_document])

    response = client.get(
        "/read_document/",
        params={"prefill": json.dumps({"document": "nope.txt"})})

    assert response.status_code == 400
    assert response.json()["detail"] == "File not found: nope.txt"


def test_traversing_file_prefill_over_http_is_rejected(client_factory):
    client = client_factory([read_document])

    response = client.get(
        "/read_document/",
        params={"prefill": json.dumps({"document": "../evil.txt"})})

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "invalid file reference '../evil.txt': is not a file of the storage "
        "directory")


def test_absolute_file_prefill_over_http_is_rejected(client_factory):
    client = client_factory([read_document])

    response = client.get(
        "/read_document/",
        params={"prefill": json.dumps({"document": "/etc/passwd"})})

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "invalid file reference '/etc/passwd': is not a file of the storage "
        "directory")


def test_wrong_extension_prefill_over_http_is_rejected(client_factory,
                                                       stored_file):
    stored_file("notes.pdf")
    client = client_factory([read_document])

    response = client.get(
        "/read_document/",
        params={"prefill": json.dumps({"document": "notes.pdf"})})

    assert response.status_code == 400
    assert response.json()["detail"].startswith(
        "document: not an accepted file type")
