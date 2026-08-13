"""The portable transport of /invoke, read by the real pipeline.

pytypehintweb 1.1.0 rewrote decode() without moving its public API: the
portable reading now belongs to the core, through schema.decode(), and the
adapter keeps only the walk that hands every file node to the host's resolver.
Nothing in src/ changed, and that is the reason to pin the transport here — a
regression in that split arrives as a value in the wrong form, never as an
import error.

What other files already cover is not repeated. str, int and bool travel
through test_http_invoke.py and test_execution.py; every plain file position
through test_files.py and test_file_resolver.py; the outgoing direction, where
a Python value becomes its browser form, through test_prefill.py and
test_open_form.py. What is left, and what this file covers, is the incoming
direction of the representations only the core can restore — the float a JSON
writer flattens to an int, a date, a time, an enum member — and the two
discriminated shapes a union arrives in, which no test sent through /invoke
before.
"""

from dataclasses import dataclass
from datetime import date, time
from pathlib import Path

import pytest

from shared import Address, Priority, TxtFile


@dataclass
class Reading:
    ratio: float
    taken: date


@dataclass
class Trip:
    origin: Address
    label: str = "trip"


@dataclass
class Note:
    document: TxtFile
    tag: str = "n"


@dataclass
class Memo:
    text: str = "m"


def told(value) -> str:
    return f"{type(value).__name__}:{value!r}"


def one_ratio(ratio: float) -> str:
    """Reports a float and the type it arrived as."""
    return told(ratio)


def many_ratios(ratios: list[float]) -> str:
    """Reports every float of a list."""
    return "|".join(told(item) for item in ratios)


def nested_ratio(reading: Reading) -> str:
    """Reports the float and the date of a dataclass."""
    return f"{told(reading.ratio)}|{told(reading.taken)}"


def one_moment(due: date, at: time) -> str:
    """Reports a date and a time."""
    return f"{told(due)}|{told(at)}"


def one_priority(priority: Priority) -> str:
    """Reports an enum member."""
    return f"{told(priority)}|{priority.value}"


def one_trip(trip: Trip) -> str:
    """Reports a dataclass nested in a dataclass."""
    return f"{trip.label}:{trip.origin.street}:{trip.origin.city}"


def one_branch(items: list[TxtFile] | list[int]) -> str:
    """Reports the branch a wrapped union arrived on."""
    return "|".join(Path(item).name if type(item) is str else told(item)
                    for item in items)


def one_row(row: Note | Memo) -> str:
    """Reports the class an inline union named."""
    return told(type(row).__name__)


SPACE = [
    one_ratio,
    many_ratios,
    nested_ratio,
    one_moment,
    one_priority,
    one_trip,
    one_branch,
    one_row,
]


@pytest.fixture
def pipeline(client_factory):
    return client_factory(SPACE)


def value_of(response):
    assert response.status_code == 200

    return response.json()["result"]["value"]


def error_of(response):
    assert response.status_code == 422

    return response.json()["error"]


def test_a_float_flattened_to_an_int_by_json_arrives_as_a_float(pipeline):
    # A JSON writer has no way to keep 1.0 apart from 1, so the browser sends
    # the int and the core restores the float the signature declares.
    assert value_of(pipeline.post("/one_ratio/invoke", json={"ratio": 1})) == (
        "float:1.0")


def test_a_float_with_a_fraction_arrives_untouched(pipeline):
    assert value_of(pipeline.post("/one_ratio/invoke",
                                  json={"ratio": 1.5})) == "float:1.5"


def test_a_flattened_float_is_restored_inside_a_list(pipeline):
    response = pipeline.post("/many_ratios/invoke", json={"ratios": [1, 2.5]})

    assert value_of(response) == "float:1.0|float:2.5"


def test_a_flattened_float_is_restored_inside_a_dataclass(pipeline):
    response = pipeline.post("/nested_ratio/invoke",
                             json={"reading": {"ratio": 3,
                                               "taken": "2026-08-01"}})

    assert value_of(response) == (
        "float:3.0|date:datetime.date(2026, 8, 1)")


def test_an_iso_date_and_time_arrive_as_their_objects(pipeline):
    response = pipeline.post("/one_moment/invoke",
                             json={"due": "2026-08-01", "at": "09:30:00"})

    assert value_of(response) == (
        "date:datetime.date(2026, 8, 1)|time:datetime.time(9, 30)")


def test_a_date_that_is_not_iso_is_unprocessable(pipeline):
    response = pipeline.post("/one_moment/invoke",
                             json={"due": "30/07/2026", "at": "09:30:00"})

    assert error_of(response) == "SchemaTypeError: due: expected date, got str"


def test_an_enum_arrives_as_the_member_its_name_points_at(pipeline):
    response = pipeline.post("/one_priority/invoke", json={"priority": "HIGH"})

    assert value_of(response) == "Priority:<Priority.HIGH: 'high'>|high"


def test_an_enum_travels_by_name_and_not_by_value(pipeline):
    # The wire carries HIGH, never "high": the value is the function's
    # business and the name is the transport.
    response = pipeline.post("/one_priority/invoke", json={"priority": "high"})

    assert error_of(response) == (
        "SchemaTypeError: priority: expected Priority, got str")


def test_a_dataclass_nested_in_a_dataclass_is_built(pipeline):
    response = pipeline.post(
        "/one_trip/invoke",
        json={"trip": {"origin": {"street": "Gran Via", "city": "Bilbao"}}})

    assert value_of(response) == "trip:Gran Via:Bilbao"


def test_an_inner_field_left_out_takes_its_own_default(pipeline):
    response = pipeline.post(
        "/one_trip/invoke",
        json={"trip": {"origin": {"street": "Gran Via"}}})

    assert value_of(response) == "trip:Gran Via:Madrid"


def test_an_inner_constraint_is_still_enforced(pipeline):
    response = pipeline.post(
        "/one_trip/invoke", json={"trip": {"origin": {"street": "ab"}}})

    assert error_of(response) == (
        "SchemaValueError: trip: origin: street: too short: 2 chars, "
        "minimum 3")


# Two options that share a runtime type keep the discriminated wrapper the
# browser sends: list[str] and list[int] are both a JSON array, so $type is
# what tells them apart. This is the shape form.js emits for a wrapped branch,
# and until now nothing in this suite sent one through /invoke.
def test_a_wrapper_takes_the_branch_its_type_names(pipeline):
    response = pipeline.post(
        "/one_branch/invoke",
        json={"items": {"$type": "list[int]", "$value": [1, 2]}})

    assert value_of(response) == "int:1|int:2"


def test_a_wrapper_reaches_the_file_branch_of_the_same_shape(pipeline,
                                                             stored_file):
    stored_file("wrapped.txt")

    response = pipeline.post(
        "/one_branch/invoke",
        json={"items": {"$type": "list[str]", "$value": ["wrapped.txt"]}})

    assert value_of(response) == "wrapped.txt"


def test_a_wrapper_naming_a_branch_that_does_not_exist_is_unprocessable(
        pipeline):
    response = pipeline.post(
        "/one_branch/invoke",
        json={"items": {"$type": "list[bool]", "$value": [True]}})

    assert error_of(response) == (
        "SchemaValueError: items: $type: not a choice: 'list[bool]', "
        "expected one of ('list[str]', 'list[int]')")


def test_the_bare_value_of_an_ambiguous_union_is_unprocessable(pipeline):
    response = pipeline.post("/one_branch/invoke", json={"items": ["a.txt"]})

    assert "items: ambiguous list" in error_of(response)


def test_the_extension_check_reaches_inside_a_wrapped_branch(pipeline,
                                                             stored_file):
    stored_file("wrapped.md")

    response = pipeline.post(
        "/one_branch/invoke",
        json={"items": {"$type": "list[str]", "$value": ["wrapped.md"]}})

    assert error_of(response) == (
        "SchemaValueError: items: $value: [0]: not an accepted file type: "
        "'wrapped.md', expected one of ('.txt',)")


def test_a_missing_reference_inside_a_wrapped_branch_is_unprocessable(
        pipeline):
    response = pipeline.post(
        "/one_branch/invoke",
        json={"items": {"$type": "list[str]", "$value": ["ghost.txt"]}})

    assert error_of(response) == "FileNotFoundError: File not found: ghost.txt"


# Dataclasses share the dict instead, so their union names itself inline: the
# $type key travels beside the fields rather than around them.
def test_an_inline_type_names_the_dataclass_that_is_built(pipeline,
                                                          stored_file):
    stored_file("inline.txt")

    response = pipeline.post(
        "/one_row/invoke",
        json={"row": {"$type": "Note", "document": "inline.txt", "tag": "z"}})

    assert value_of(response) == "str:'Note'"


def test_the_other_inline_class_is_built_from_its_own_fields(pipeline):
    response = pipeline.post("/one_row/invoke",
                             json={"row": {"$type": "Memo", "text": "t"}})

    assert value_of(response) == "str:'Memo'"


def test_an_inline_type_naming_no_class_of_the_union_is_unprocessable(
        pipeline):
    response = pipeline.post("/one_row/invoke",
                             json={"row": {"$type": "Ghost", "text": "t"}})

    assert error_of(response) == (
        "SchemaValueError: row: $type: not a choice: 'Ghost', expected one of "
        "('Note', 'Memo')")


def test_a_dataclass_union_without_its_type_is_unprocessable(pipeline,
                                                             stored_file):
    stored_file("inline.txt")

    response = pipeline.post("/one_row/invoke",
                             json={"row": {"document": "inline.txt"}})

    assert "row: ambiguous dict" in error_of(response)


def test_the_extension_check_reaches_inside_an_inline_class(pipeline,
                                                            stored_file):
    stored_file("inline.md")

    response = pipeline.post(
        "/one_row/invoke",
        json={"row": {"$type": "Note", "document": "inline.md"}})

    assert error_of(response) == (
        "SchemaValueError: row: document: not an accepted file type: "
        "'inline.md', expected one of ('.txt',)")


def test_every_discriminated_shape_agrees_over_the_stream(pipeline, sse):
    bodies = [
        {"items": {"$type": "list[int]", "$value": [1]}},
        {"items": {"$type": "list[bool]", "$value": [True]}},
    ]

    for body in bodies:
        direct = pipeline.post("/one_branch/invoke", json=body)
        streamed = pipeline.post("/one_branch/invoke-stream", json=body)

        assert sse(streamed.text)[-1] == ("result", direct.json())
