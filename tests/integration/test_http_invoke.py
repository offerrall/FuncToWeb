import json
from typing import Annotated
from urllib.parse import parse_qs, urlparse

import pytest

from func_to_web import Download, OpenForm

BIG = 200_000


def echo(text: str = "hola") -> str:
    return f"{text}!"


def widening(size: int = 10) -> str:
    return "x" * size


def listing(a: int = 1) -> list[str]:
    return ["one", "two", "three"]


def bundle(a: int = 1) -> Annotated[bytes, Download(filename="report.bin")]:
    return b"payload"


def confirm(name: str = "x") -> str:
    return name


def prepare(a: int = 1) -> Annotated[dict, OpenForm(confirm)]:
    return {"name": "Ana"}


SPACE = [echo, widening, listing, bundle, confirm, prepare]

NOT_AN_OBJECT = [
    ("array", b"[1, 2]"),
    ("scalar", b"5"),
    ("string", b'"hello"'),
    ("null", b"null"),
    ("loose text", b"hello"),
    ("empty", b""),
    ("utf-16 bom", b"\xff\xfe"),
    ("invalid utf-8", b"\xff"),
    ("invalid utf-8 inside a string", b'{"a": "\xff"}'),
]


@pytest.fixture
def surface(client_factory):
    return client_factory(SPACE)


@pytest.fixture
def adder(client_factory, scalar):
    return client_factory(scalar)


def json_post(client, path, raw, content_type="application/json"):
    headers = {} if content_type is None else {"content-type": content_type}

    return client.post(path, content=raw, headers=headers)


def test_valid_json_object_is_accepted(adder):
    response = adder.post("/add/invoke", json={"a": 1, "b": 3})

    assert response.status_code == 200
    assert response.json() == {"result": {"type": "text", "value": "4"}}


def test_absent_optional_field_takes_its_default(adder):
    assert adder.post("/add/invoke", json={"a": 1}).json() == {
        "result": {"type": "text", "value": "3"}
    }


def test_missing_required_field_breaks_the_contract(adder):
    response = adder.post("/add/invoke", json={})

    assert response.status_code == 422
    assert response.json() == {"error": "SchemaTypeError: missing argument(s): a"}


def test_unknown_extra_field_breaks_the_contract(adder):
    response = adder.post("/add/invoke", json={"a": 1, "ghost": 9})

    assert response.status_code == 422
    assert response.json() == {
        "error": "SchemaTypeError: unexpected argument(s): ghost"
    }


@pytest.mark.parametrize(("label", "raw"), NOT_AN_OBJECT)
def test_body_that_is_not_a_json_object_gets_a_transport_error(adder, label, raw):
    response = json_post(adder, "/add/invoke", raw)

    assert response.status_code == 422
    assert set(response.json()) == {"detail"}
    assert response.json()["detail"] in {
        "body must be valid JSON",
        "body must be a JSON object",
    }


def test_transport_error_and_contract_error_are_different_shapes(adder):
    transport_error = json_post(adder, "/add/invoke", b"[1, 2]")
    contract_error = adder.post("/add/invoke", json={})

    assert transport_error.status_code == contract_error.status_code == 422
    assert "error" not in transport_error.json()
    assert "detail" not in contract_error.json()


def test_empty_body_reports_a_missing_body(adder):
    detail = json_post(adder, "/add/invoke", b"").json()["detail"]

    assert detail == "body must be valid JSON"


# json.loads decodes the bytes itself, so a body that is not UTF-8 raises
# UnicodeDecodeError and not JSONDecodeError. b"\xff\xfe" is not one of them:
# it is the UTF-16 BOM, which json.detect_encoding reads and answers for. These
# three do reach the decoder, and an uncaught one is a 500.
@pytest.mark.parametrize("raw", [b"\xff", b"\x80\x81", b'{"a": "\xff"}'])
def test_body_that_is_not_utf_8_reports_invalid_json(adder, raw):
    response = json_post(adder, "/add/invoke", raw)

    assert response.status_code == 422
    assert response.json() == {"detail": "body must be valid JSON"}


@pytest.mark.parametrize("raw", [b"\xff", b"\x80\x81", b'{"a": "\xff"}'])
def test_a_body_that_is_not_utf_8_is_refused_by_the_stream_route_too(adder, raw):
    response = json_post(adder, "/add/invoke-stream", raw)

    assert response.status_code == 422
    assert response.json() == {"detail": "body must be valid JSON"}


def test_loose_text_body_reports_invalid_json(adder):
    detail = json_post(adder, "/add/invoke", b"hello").json()["detail"]

    assert detail == "body must be valid JSON"


def test_array_body_reports_a_wrong_body_type(adder):
    detail = json_post(adder, "/add/invoke", b"[1, 2]").json()["detail"]

    assert detail == "body must be a JSON object"


def test_json_content_type_is_accepted(adder):
    response = json_post(adder, "/add/invoke", b'{"a": 1}')

    assert response.status_code == 200


def test_absent_content_type_is_accepted(adder):
    response = json_post(adder, "/add/invoke", b'{"a": 1}', content_type=None)

    assert response.status_code == 200
    assert response.json() == {"result": {"type": "text", "value": "3"}}


def test_text_content_type_does_not_override_a_valid_json_body(adder):
    response = json_post(adder, "/add/invoke", b'{"a": 1}',
                         content_type="text/plain")

    assert response.status_code == 200


def test_get_is_not_allowed_on_the_route(adder):
    assert adder.get("/add/invoke").status_code == 405


def test_unknown_slug_is_not_found(adder):
    assert adder.post("/ghost/invoke", json={}).status_code == 404


def test_trailing_slash_redirects_to_the_canonical_path(adder):
    response = adder.post("/add/invoke/", json={"a": 1},
                          follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].endswith("/add/invoke")


def test_trailing_slash_reaches_the_function_when_followed(adder):
    response = adder.post("/add/invoke/", json={"a": 1})

    assert response.status_code == 200
    assert response.json() == {"result": {"type": "text", "value": "3"}}


def test_route_works_under_a_prefix(client_factory, scalar):
    client = client_factory(scalar, prefix="/api")

    assert client.post("/api/add/invoke", json={"a": 1}).status_code == 200
    assert client.post("/add/invoke", json={"a": 1}).status_code == 404


def test_function_exception_answers_500(client_factory, failing):
    client = client_factory(failing)
    response = client.post("/boom/invoke", json={})

    assert response.status_code == 500
    assert response.json() == {"error": "RuntimeError: boom"}


def test_unicode_travels_in_and_out(surface):
    response = surface.post("/echo/invoke", json={"text": "ñandú 你好"})

    assert response.json() == {"result": {"type": "text", "value": "ñandú 你好!"}}
    assert "ñandú 你好!".encode("utf-8") in response.content


def test_a_large_result_is_returned_whole(surface):
    result = surface.post("/widening/invoke", json={"size": BIG}).json()["result"]

    assert result["value"] == "x" * BIG


def test_a_list_of_outputs_keeps_the_return_order(surface):
    result = surface.post("/listing/invoke", json={}).json()["result"]

    assert [item["value"] for item in result] == ["one", "two", "three"]


def test_a_download_output_is_fetchable_by_its_reference(surface):
    result = surface.post("/bundle/invoke", json={}).json()["result"]
    fetched = surface.get(f"/returns/{result['value']}")

    assert result["type"] == "download"
    assert result["filename"] == "report.bin"
    assert fetched.status_code == 200
    assert fetched.content == b"payload"


def test_a_form_output_points_at_the_prefilled_target(surface):
    result = surface.post("/prepare/invoke", json={}).json()["result"]
    query = parse_qs(urlparse(result["href"]).query)

    assert result["type"] == "form"
    assert result["href"].startswith("../confirm/?")
    assert json.loads(query["prefill"][0]) == {"name": "Ana"}
    assert surface.get("/confirm/", params={"prefill": query["prefill"][0]}).status_code == 200


def test_every_answer_is_json(client_factory, scalar, failing):
    client = client_factory([scalar, failing])
    answers = [
        client.post("/add/invoke", json={"a": 1}),
        client.post("/add/invoke", json={"ghost": 1}),
        client.post("/boom/invoke", json={}),
    ]

    assert [answer.status_code for answer in answers] == [200, 422, 500]
    assert {answer.headers["content-type"] for answer in answers} == {
        "application/json"
    }


def test_an_answer_is_never_cached(adder):
    response = adder.post("/add/invoke", json={"a": 1})

    assert "cache-control" not in response.headers
    assert "etag" not in response.headers


def test_doc_presents_invoke_as_the_call_for_non_streaming_clients(adder):
    text = adder.get("/doc").text
    calling = text.index("=== Calling ===")
    invoke = text.index("POST <base_url>/<slug>/invoke\n")
    stream = text.index("POST <base_url>/<slug>/invoke-stream")

    assert calling < invoke < stream
    assert "SSE for progress" in text[stream:]
    assert "the same call" in text[stream:]
