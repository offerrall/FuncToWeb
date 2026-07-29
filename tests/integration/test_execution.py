import json
from pathlib import Path
from typing import Annotated
from urllib.parse import parse_qs, urlparse

import pytest

from func_to_web import Download, IsPathFile, Min, OpenForm

TxtFile = Annotated[str, IsPathFile(extensions=(".txt",))]


def adding(a: int, b: int = 2) -> int:
    return a + b


async def doubled(a: int = 3) -> str:
    return str(a * 2)


def exploding(a: int = 1) -> str:
    raise RuntimeError("boom")


async def exploding_async(a: int = 1) -> str:
    raise ValueError("async boom")


def nothing(a: int = 1) -> None:
    return None


def listing(a: int = 1) -> list[str]:
    return ["one", "two"]


def pairing(a: int = 1) -> tuple:
    return ("x", "y")


def emptying(a: int = 1) -> list:
    return []


def reading(document: TxtFile) -> str:
    return Path(document).read_text(encoding="utf-8")


def bounded(a: Annotated[int, Min(10)] = 10) -> int:
    return a


def bundle(a: int = 1) -> Annotated[bytes, Download(filename="report.bin")]:
    return b"payload"


def broken_download(a: int = 1) -> Annotated[Path, Download(filename="r.txt")]:
    return 7


def looping(a: int = 1) -> list:
    outputs = []
    outputs.append(outputs)
    return outputs


def confirm(name: str = "x") -> str:
    return name


def prepare(a: int = 1) -> Annotated[dict, OpenForm(confirm)]:
    return {"name": "Ana"}


def prepare_badly(a: int = 1) -> Annotated[dict, OpenForm(confirm)]:
    return 7


SPACE = [
    adding,
    doubled,
    exploding,
    exploding_async,
    nothing,
    listing,
    pairing,
    emptying,
    reading,
    bounded,
    bundle,
    broken_download,
    looping,
    confirm,
    prepare,
    prepare_badly,
]

SUCCESS = ("/adding/invoke", {"a": 1})
DECODE_FAILURE = ("/reading/invoke", {"document": "missing.txt"})
BUILD_FAILURE = ("/bounded/invoke", {"a": 1})
RAISING = ("/exploding/invoke", {})
RETURN_FAILURE = ("/broken-download/invoke", {})
OUTPUT_FAILURE = ("/looping/invoke", {})

STATUS_MATRIX = [
    (*SUCCESS, 200),
    ("/doubled/invoke", {}, 200),
    ("/bundle/invoke", {}, 200),
    ("/prepare/invoke", {}, 200),
    (*DECODE_FAILURE, 422),
    (*BUILD_FAILURE, 422),
    ("/adding/invoke", {}, 422),
    ("/adding/invoke", {"a": 1, "ghost": 3}, 422),
    (*RAISING, 500),
    ("/exploding-async/invoke", {}, 500),
    (*RETURN_FAILURE, 500),
    (*OUTPUT_FAILURE, 500),
    ("/prepare-badly/invoke", {}, 500),
]

FAILING_MATRIX = [case for case in STATUS_MATRIX if case[2] != 200]


@pytest.fixture
def pipeline(client_factory):
    return client_factory(SPACE)


def result_of(response):
    payload = response.json()

    assert set(payload) == {"result"}

    return payload["result"]


def error_of(response):
    payload = response.json()

    assert set(payload) == {"error"}

    return payload["error"]


def without_reference(envelope):
    result = envelope.get("result")

    if type(result) is dict and result.get("type") == "download":
        return {"result": {**result, "value": "<reference>"}}

    return envelope


def final_event(client, path, body, sse):
    response = client.post(path, json=body)

    assert response.status_code == 200

    events = sse(response.text)

    assert events[-1][0] == "result"

    return events[-1][1]


def test_sync_function_runs_and_returns_its_output(pipeline):
    response = pipeline.post("/adding/invoke", json={"a": 1})

    assert response.status_code == 200
    assert result_of(response) == {"type": "text", "value": "3"}


def test_async_function_runs_and_returns_its_output(pipeline):
    response = pipeline.post("/doubled/invoke", json={"a": 4})

    assert response.status_code == 200
    assert result_of(response) == {"type": "text", "value": "8"}


def test_single_return_becomes_one_output_object(pipeline):
    assert result_of(pipeline.post("/adding/invoke", json={"a": 5})) == {
        "type": "text",
        "value": "7",
    }


def test_list_return_becomes_a_list_of_outputs_in_order(pipeline):
    assert result_of(pipeline.post("/listing/invoke", json={})) == [
        {"type": "text", "value": "one"},
        {"type": "text", "value": "two"},
    ]


def test_tuple_return_becomes_a_list_of_outputs_in_order(pipeline):
    assert result_of(pipeline.post("/pairing/invoke", json={})) == [
        {"type": "text", "value": "x"},
        {"type": "text", "value": "y"},
    ]


def test_none_return_is_a_success_with_a_done_text(pipeline):
    response = pipeline.post("/nothing/invoke", json={})

    assert response.status_code == 200
    assert result_of(response) == {"type": "text", "value": "Done"}


def test_empty_collection_return_is_a_success(pipeline):
    response = pipeline.post("/emptying/invoke", json={})

    assert response.status_code == 200
    assert result_of(response) == {"type": "text", "value": "Done"}


def test_download_return_becomes_a_download_output(pipeline, returns_dir):
    response = pipeline.post("/bundle/invoke", json={})
    result = result_of(response)

    assert response.status_code == 200
    assert result["type"] == "download"
    assert result["filename"] == "report.bin"
    assert (returns_dir / result["value"]).read_bytes() == b"payload"


def test_open_form_return_becomes_a_form_output(pipeline):
    result = result_of(pipeline.post("/prepare/invoke", json={}))
    query = parse_qs(urlparse(result["href"]).query)

    assert result["type"] == "form"
    assert result["href"].startswith("../confirm/?")
    assert json.loads(query["prefill"][0]) == {"name": "Ana"}


def test_decoded_file_reference_reaches_the_function(pipeline, stored_file):
    stored_file(name="note.txt", data="hola".encode("utf-8"))

    response = pipeline.post("/reading/invoke", json={"document": "note.txt"})

    assert response.status_code == 200
    assert result_of(response) == {"type": "text", "value": "hola"}


def test_raising_function_answers_500_with_its_exception(pipeline):
    response = pipeline.post("/exploding/invoke", json={})

    assert response.status_code == 500
    assert error_of(response) == "RuntimeError: boom"


def test_raising_async_function_answers_500_with_its_exception(pipeline):
    response = pipeline.post("/exploding-async/invoke", json={})

    assert response.status_code == 500
    assert error_of(response) == "ValueError: async boom"


def test_decode_failure_answers_422(pipeline):
    response = pipeline.post("/reading/invoke", json={"document": "gone.txt"})

    assert response.status_code == 422
    assert error_of(response) == "FileNotFoundError: File not found: gone.txt"


def test_build_failure_answers_422(pipeline):
    response = pipeline.post("/bounded/invoke", json={"a": 1})

    assert response.status_code == 422
    assert error_of(response) == "SchemaValueError: a: too small: 1, minimum 10"


def test_return_parser_failure_answers_500(pipeline):
    response = pipeline.post("/broken-download/invoke", json={})

    assert response.status_code == 500
    assert error_of(response) == "ReturnContractError: expected Path for Download, got int"


def test_output_parser_failure_answers_500(pipeline):
    response = pipeline.post("/looping/invoke", json={})

    assert response.status_code == 500
    assert error_of(response) == "ReturnContractError: recursive output collection"


def test_open_form_return_failure_answers_500(pipeline):
    response = pipeline.post("/prepare-badly/invoke", json={})

    assert response.status_code == 500
    assert error_of(response) == (
        "ReturnContractError: OpenForm return must be a mapping or dataclass "
        "instance"
    )


@pytest.mark.parametrize(("path", "body", "status"), STATUS_MATRIX)
def test_status_matrix(pipeline, path, body, status):
    assert pipeline.post(path, json=body).status_code == status


@pytest.mark.parametrize(("path", "body", "status"), STATUS_MATRIX)
def test_envelope_carries_exactly_one_key(pipeline, path, body, status):
    payload = pipeline.post(path, json=body).json()

    assert set(payload) == ({"result"} if status == 200 else {"error"})


@pytest.mark.parametrize(("path", "body", "status"), FAILING_MATRIX)
def test_error_message_names_its_exception_type(pipeline, path, body, status):
    message = error_of(pipeline.post(path, json=body))
    kind, separator, text = message.partition(": ")

    assert separator == ": "
    assert kind.isidentifier()
    assert text


def test_function_is_not_called_when_decoding_fails(client_factory):
    calls = []

    def tracking(document: TxtFile) -> str:
        calls.append(document)
        return document

    client = client_factory(tracking)
    response = client.post("/tracking/invoke", json={"document": "gone.txt"})

    assert response.status_code == 422
    assert calls == []


def test_function_is_not_called_when_building_fails(client_factory):
    calls = []

    def tracking(a: Annotated[int, Min(10)] = 10) -> str:
        calls.append(a)
        return str(a)

    client = client_factory(tracking)

    assert client.post("/tracking/invoke", json={"a": 1}).status_code == 422
    assert client.post("/tracking/invoke", json={"ghost": 1}).status_code == 422
    assert client.post("/tracking/invoke", json={"a": "x"}).status_code == 422
    assert calls == []


def test_output_is_built_once(client_factory):
    renders = []

    class Rendered:
        def __str__(self):
            renders.append(1)
            return "rendered"

    def producing(a: int = 1) -> Rendered:
        return Rendered()

    client = client_factory(producing)
    response = client.post("/producing/invoke", json={})

    assert result_of(response) == {"type": "text", "value": "rendered"}
    assert renders == [1]


def test_download_output_is_stored_once(pipeline, returns_dir):
    pipeline.post("/bundle/invoke", json={})

    assert len(list(returns_dir.iterdir())) == 1


def test_stream_shares_the_success_envelope_of_invoke(pipeline, sse):
    direct = pipeline.post("/adding/invoke", json={"a": 1})
    streamed = final_event(pipeline, "/adding/invoke-stream", {"a": 1}, sse)

    assert direct.json() == streamed


def test_stream_shares_the_error_envelope_of_invoke(pipeline, sse):
    direct = pipeline.post("/bounded/invoke", json={"a": 1})
    streamed = final_event(pipeline, "/bounded/invoke-stream", {"a": 1}, sse)

    assert direct.status_code == 422
    assert direct.json() == streamed


def test_stream_answers_200_for_a_body_invoke_rejects_with_422(pipeline, sse):
    body = {"a": 1}
    streamed = pipeline.post("/bounded/invoke-stream", json=body)

    assert pipeline.post("/bounded/invoke", json=body).status_code == 422
    assert streamed.status_code == 200
    assert sse(streamed.text)[-1][1] == {
        "error": "SchemaValueError: a: too small: 1, minimum 10"
    }


@pytest.mark.parametrize(("path", "body", "status"), STATUS_MATRIX)
def test_stream_and_invoke_agree_on_every_case(pipeline, sse, path, body, status):
    direct = pipeline.post(path, json=body).json()
    streamed = final_event(pipeline, f"{path}-stream", body, sse)

    assert without_reference(direct) == without_reference(streamed)
