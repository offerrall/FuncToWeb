"""Tuples and @immutable models as parameters, from the plan to the call.

pytypehintweb 1.4.0 gives a form to the tuples a list describes, and
pytypehint's @immutable models hold their collections in tuples, so a
function may take either and receive real tuples and real instances.
"""

from typing import Annotated

import pytest

from func_to_web import Max, Min, WebFunction, immutable

Channel = Annotated[float, Min(0.0), Max(1.0)]


@immutable
class Layer:
    name: Annotated[str, Min(1)]
    color: tuple[Channel, Channel, Channel] = (0.0, 0.0, 1.0)
    tags: tuple[str, ...] = ()


def mean(values: Annotated[tuple[float, ...], Min(1), Max(4)]) -> str:
    return f"{type(values).__name__} {sum(values) / len(values)}"


def mix(color: tuple[Channel, Channel, Channel] = (1.0, 0.5, 0.0)) -> str:
    return f"{type(color).__name__} {color}"


def describe(layer: Layer) -> str:
    return (f"{type(layer).__name__} {layer.name} "
            f"{type(layer.color).__name__} {layer.color} {layer.tags}")


def either(values: list[int] | tuple[int, ...]) -> str:
    return type(values).__name__


def invoke(client_factory, fn, body):
    response = client_factory([fn]).post(f"/{fn.__name__}/invoke", json=body)

    return response.status_code, response.json()


def test_a_variadic_tuple_is_a_bounded_list_in_the_plan():
    node = WebFunction(mean).plan["fields"][0]["node"]

    assert (node["kind"], node["minItems"], node["maxItems"]) == ("list", 1, 4)
    assert node["item"]["kind"] == "float"


def test_a_same_typed_fixed_tuple_is_a_list_of_exactly_its_size():
    field = WebFunction(mix).plan["fields"][0]

    assert (field["node"]["minItems"], field["node"]["maxItems"]) == (3, 3)
    assert field["default"] == [1.0, 0.5, 0.0]


def test_the_function_receives_a_real_tuple(client_factory):
    assert invoke(client_factory, mean, {"values": [1, 2.5]}) == (
        200, {"result": {"type": "text", "value": "tuple 1.75"}})
    assert invoke(client_factory, mix, {"color": [0.25, 0.5, 1]}) == (
        200, {"result": {"type": "text", "value": "tuple (0.25, 0.5, 1.0)"}})
    assert invoke(client_factory, mix, {}) == (
        200, {"result": {"type": "text", "value": "tuple (1.0, 0.5, 0.0)"}})


@pytest.mark.parametrize("fn, body, fragment", [
    (mean, {"values": []}, "values: too few items: 0, minimum 1"),
    (mean, {"values": [1.0] * 5}, "values: too many items: 5, maximum 4"),
    (mix, {"color": [0.1, 0.2]}, "color: expected 3 items, got 2"),
    (mix, {"color": [0.1, 0.2, 2.0]}, "color: [2]: too large: 2.0, maximum 1.0"),
])
def test_a_tuple_that_breaks_its_contract_is_a_422(client_factory, fn, body,
                                                   fragment):
    status, envelope = invoke(client_factory, fn, body)

    assert status == 422
    assert fragment in envelope["error"]


def test_an_immutable_model_arrives_built_with_its_tuples(client_factory):
    status, envelope = invoke(client_factory, describe, {
        "layer": {"name": "Photo", "color": [1, 0, 0], "tags": ["a", "b"]},
    })

    assert (status, envelope["result"]["value"]) == (
        200, "Layer Photo tuple (1.0, 0.0, 0.0) ('a', 'b')")

    status, envelope = invoke(client_factory, describe,
                              {"layer": {"name": "Plain"}})

    assert (status, envelope["result"]["value"]) == (
        200, "Layer Plain tuple (0.0, 0.0, 1.0) ()")


def test_an_immutable_model_validates_what_it_is_given(client_factory):
    status, envelope = invoke(client_factory, describe,
                              {"layer": {"name": "", "color": [0, 0, 0]}})

    assert status == 422
    assert "layer: name: too short" in envelope["error"]


def test_a_list_and_a_tuple_in_one_union_are_named_on_the_wire(client_factory):
    assert invoke(client_factory, either, {
        "values": {"$type": "tuple[int, ...]", "$value": [1, 2]},
    }) == (200, {"result": {"type": "text", "value": "tuple"}})
    assert invoke(client_factory, either, {
        "values": {"$type": "list[int]", "$value": [1, 2]},
    }) == (200, {"result": {"type": "text", "value": "list"}})


def test_a_tuple_whose_positions_differ_is_refused_when_prepared():
    def pair(value: tuple[int, str]) -> str:
        return str(value)

    with pytest.raises(TypeError, match=r"fields\.value: tuple\[int, str\]"):
        WebFunction(pair)
