from collections import namedtuple
from enum import Enum

import pytest

from func_to_web import ReturnContractError
from func_to_web.outputs import output_of, outputs_of, text_output


class Priority(Enum):
    LOW = "low"
    HIGH = "high"


class Named:
    def __str__(self):
        return "custom text"


class Exploding:
    def __str__(self):
        raise ValueError("no text available")


Point = namedtuple("Point", "x y")


def values_of(outputs):
    return [output["value"] for output in outputs]


def test_text_output_builds_a_text_block():
    assert text_output("hello") == {"type": "text", "value": "hello"}


def test_none_becomes_done():
    assert output_of(None) == {"type": "text", "value": "Done"}


def test_empty_string_stays_empty():
    assert output_of("") == {"type": "text", "value": ""}


def test_string_travels_unchanged():
    assert output_of("hello") == {"type": "text", "value": "hello"}


def test_integer_uses_str():
    assert output_of(42) == {"type": "text", "value": "42"}


def test_float_uses_str():
    assert output_of(2.5) == {"type": "text", "value": "2.5"}


def test_bool_uses_str():
    assert output_of(True) == {"type": "text", "value": "True"}


def test_enum_member_uses_str():
    assert output_of(Priority.LOW) == {"type": "text", "value": "Priority.LOW"}


def test_custom_str_is_respected():
    assert output_of(Named()) == {"type": "text", "value": "custom text"}


def test_dict_uses_its_repr():
    assert output_of({"a": 1}) == {"type": "text", "value": "{'a': 1}"}


def test_empty_list_becomes_done():
    assert output_of([]) == {"type": "text", "value": "Done"}


def test_empty_tuple_becomes_done():
    assert output_of(()) == {"type": "text", "value": "Done"}


def test_single_item_list_still_produces_a_list_of_outputs():
    assert output_of(["only"]) == [{"type": "text", "value": "only"}]


def test_single_item_tuple_still_produces_a_list_of_outputs():
    assert output_of(("only",)) == [{"type": "text", "value": "only"}]


def test_simple_value_produces_a_single_output():
    result = output_of("only")

    assert type(result) is dict


def test_outputs_of_always_returns_a_list():
    assert outputs_of("only") == [{"type": "text", "value": "only"}]


def test_nested_lists_are_flattened():
    assert values_of(output_of([1, [2, [3, 4]]])) == ["1", "2", "3", "4"]


def test_nested_tuples_are_flattened():
    assert values_of(output_of((1, (2, (3, 4))))) == ["1", "2", "3", "4"]


def test_mixed_list_and_tuple_are_flattened():
    assert values_of(output_of([1, (2, [3])])) == ["1", "2", "3"]


def test_none_inside_a_collection_becomes_done():
    assert values_of(output_of([None, 1])) == ["Done", "1"]


def test_empty_collection_inside_a_collection_becomes_done():
    assert values_of(output_of([[], 1])) == ["Done", "1"]


def test_several_outputs_keep_their_order():
    assert values_of(output_of(["first", "second", "third"])) == [
        "first",
        "second",
        "third",
    ]


def test_repeated_reference_is_not_a_cycle():
    shared = ["value"]

    assert values_of(output_of([shared, shared])) == ["value", "value"]


def test_direct_cycle_is_rejected():
    looping = []
    looping.append(looping)

    with pytest.raises(ReturnContractError,
                       match="recursive output collection"):
        output_of(looping)


def test_indirect_cycle_is_rejected():
    outer = []
    inner = [outer]
    outer.append(inner)

    with pytest.raises(ReturnContractError,
                       match="recursive output collection"):
        output_of(outer)


def test_script_tag_travels_as_plain_text():
    payload = "<script>alert(1)</script>"

    assert output_of(payload) == {"type": "text", "value": payload}


def test_script_tag_inside_a_collection_travels_as_plain_text():
    payload = "<img src=x onerror=alert(1)>"

    assert values_of(output_of([payload])) == [payload]


def test_failing_str_propagates_the_original_error():
    with pytest.raises(ValueError, match="no text available"):
        output_of(Exploding())


def test_plain_list_is_not_turned_into_a_table():
    outputs = output_of([[1, 2], [3, 4]])

    assert [output["type"] for output in outputs] == ["text"] * 4


def test_list_of_dicts_is_one_text_per_dict():
    outputs = output_of([{"name": "Ana"}, {"name": "Bea"}])

    assert values_of(outputs) == ["{'name': 'Ana'}", "{'name': 'Bea'}"]


def test_tuple_subclass_is_a_single_text_output():
    point = Point(1, 2)

    assert output_of(point) == {"type": "text", "value": str(point)}


def test_text_value_is_always_a_string():
    outputs = outputs_of([1, 2.5, True, None])

    assert all(type(output["value"]) is str for output in outputs)


def test_download_hook_replaces_a_simple_value():
    marker = {"type": "download", "value": "ref", "filename": "f.txt"}

    assert output_of(object(), download=lambda value: marker) == marker


def test_download_hook_returning_none_falls_back_to_text():
    assert output_of("plain", download=lambda value: None) == {
        "type": "text",
        "value": "plain",
    }


def test_download_hook_is_not_consulted_for_none():
    def refuse(value):
        raise AssertionError("hook must not run for None")

    assert output_of(None, download=refuse) == {"type": "text",
                                                "value": "Done"}


def test_download_hook_runs_for_every_item_of_a_collection():
    seen = []

    def record(value):
        seen.append(value)
        return None

    output_of([1, [2]], download=record)

    assert seen == [1, 2]
