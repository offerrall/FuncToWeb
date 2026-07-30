from pathlib import Path
from typing import Annotated

import pytest

from func_to_web import Download
from func_to_web.outputs import download_output
from func_to_web.web import returned_files
from func_to_web.web.references import (
    FILENAME_LIMIT,
    REFERENCE_LIMIT,
    RETURN_LIMIT,
)
from func_to_web.web.returned_files import store, stored_return
from shared import carries

SEPARATORS = ["../secret.txt", "..\\secret.txt", "/etc/passwd",
              "sub/secret.txt", "..", "."]

ENCODED = ["%2e%2e%2fsecret.txt", "..%2Fsecret.txt", "%2e%2e%5csecret.txt"]

TRAVERSALS = SEPARATORS + ENCODED


def path_function(source):
    def send_file(times: int = 1) -> Annotated[Path, Download()]:
        return source

    return send_file


def named_function(source, name):
    def send_fixed(times: int = 1) -> Annotated[Path,
                                                Download(filename=name)]:
        return source

    return send_fixed


def text_function(source):
    def send_text_path(times: int = 1) -> Annotated[str, Download()]:
        return str(source)

    return send_text_path


def bytes_function(payload, name):
    def send_bytes(times: int = 1) -> Annotated[bytes,
                                                Download(filename=name)]:
        return payload

    return send_bytes


def plain_function(times: int = 1) -> str:
    return "no downloads here"


def invoke(client, slug, prefix=""):
    response = client.post(f"{prefix}/{slug}/invoke", json={"times": 1})

    assert response.status_code == 200

    return response.json()["result"]


def test_download_output_builds_a_download_block():
    assert download_output("abc.report.pdf", "report.pdf") == {
        "type": "download",
        "value": "abc.report.pdf",
        "filename": "report.pdf",
    }


def test_store_from_path_keeps_the_content(returns_dir, sized_file):
    source = sized_file("report.txt", data=b"payload")

    reference = store(source, "report.txt")

    assert (returns_dir / reference).read_bytes() == b"payload"


def test_store_from_bytes_writes_the_content(returns_dir):
    reference = store(b"in memory", "memory.bin")

    assert (returns_dir / reference).read_bytes() == b"in memory"


def test_store_keeps_the_original_name_in_the_reference(sized_file):
    source = sized_file("report.txt", data=b"x")

    assert stored_return(store(source, "report.txt"))[1] == "report.txt"


def test_store_uses_the_explicit_name(sized_file):
    source = sized_file("internal-1234.tmp", data=b"x")

    reference = store(source, "report.pdf")

    assert stored_return(reference)[1] == "report.pdf"


def test_repeated_names_produce_distinct_references(returns_dir):
    first = store(b"one", "same.txt")
    second = store(b"two", "same.txt")

    assert first != second
    assert (returns_dir / first).read_bytes() == b"one"
    assert (returns_dir / second).read_bytes() == b"two"


def test_reference_carries_no_local_path(sized_file):
    source = sized_file("report.txt", data=b"x")

    reference = store(source, "report.txt")

    assert "/" not in reference
    assert "\\" not in reference
    assert str(source.parent) not in reference


def test_stored_return_resolves_the_path_and_the_public_name(returns_dir):
    reference = store(b"x", "report.pdf")

    path, filename = stored_return(reference)

    assert path == returns_dir / reference
    assert filename == "report.pdf"


def test_a_long_filename_is_still_served_back(returns_dir):
    # The pending prefix only exists under UPLOADS_DIR, so the shorter
    # reference limit it forces must not reach what /returns already minted.
    reference = store(b"x", "r" * (FILENAME_LIMIT - 4) + ".pdf")

    path, filename = stored_return(reference)

    assert len(reference.encode("utf-8")) > REFERENCE_LIMIT
    assert len(reference.encode("utf-8")) <= RETURN_LIMIT
    assert path == returns_dir / reference
    assert filename == "r" * (FILENAME_LIMIT - 4) + ".pdf"


def test_a_reference_past_the_return_limit_is_refused(returns_dir):
    # Longer than this and even the .part of publishing breaks NAME_MAX, so
    # store() could not have written it in the first place.
    with pytest.raises(ValueError, match=f"longer than {RETURN_LIMIT} bytes"):
        stored_return("r" * (RETURN_LIMIT + 1) + ".pdf")


def test_original_file_is_never_moved(sized_file):
    source = sized_file("report.txt", data=b"payload")

    store(source, "report.txt")

    assert source.read_bytes() == b"payload"


def test_missing_source_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError):
        store(tmp_path / "absent.txt", "absent.txt")


def test_directory_source_is_reported(tmp_path):
    with pytest.raises(IsADirectoryError):
        store(tmp_path, "folder.txt")


def test_empty_bytes_are_stored(returns_dir):
    reference = store(b"", "empty.bin")

    assert (returns_dir / reference).read_bytes() == b""


def test_large_file_survives_the_round_trip(returns_dir, sized_file):
    payload = bytes(range(256)) * 1400
    source = sized_file("big.bin", data=payload)

    reference = store(source, "big.bin")

    assert (returns_dir / reference).read_bytes() == payload


def test_failed_write_leaves_no_partial_file(returns_dir, sized_file,
                                             monkeypatch):
    def refuse(source, target):
        raise OSError("no space left on device")

    monkeypatch.setattr(returned_files, "copyfile", refuse)
    source = sized_file("report.txt", data=b"x")

    with pytest.raises(OSError, match="no space left"):
        store(source, "report.txt")

    assert list(returns_dir.iterdir()) == []


def test_unknown_reference_is_reported():
    with pytest.raises(FileNotFoundError):
        stored_return("deadbeef.report.pdf")


@pytest.mark.parametrize("reference", SEPARATORS)
def test_reference_with_separators_is_rejected(reference):
    with pytest.raises(ValueError):
        stored_return(reference)


@pytest.mark.parametrize("reference", ENCODED)
def test_encoded_traversal_is_never_decoded_into_a_path(reference):
    with pytest.raises(FileNotFoundError):
        stored_return(reference)


def test_empty_reference_is_rejected():
    with pytest.raises(ValueError):
        stored_return("")


def test_download_is_served_from_the_returns_route(client_factory, sized_file):
    source = sized_file("report.txt", data=b"payload")
    client = client_factory(path_function(source))

    result = invoke(client, "send_file")
    response = client.get(f"/returns/{result['value']}")

    assert response.status_code == 200
    assert response.content == b"payload"


def test_download_result_has_the_download_shape(client_factory, sized_file):
    source = sized_file("report.txt", data=b"payload")
    client = client_factory(path_function(source))

    result = invoke(client, "send_file")

    assert result["type"] == "download"
    assert result["filename"] == "report.txt"


def test_download_is_served_under_a_prefix(client_factory, sized_file):
    source = sized_file("report.txt", data=b"payload")
    client = client_factory(path_function(source), prefix="/tools")

    result = invoke(client, "send_file", prefix="/tools")
    response = client.get(f"/tools/returns/{result['value']}")

    assert response.status_code == 200
    assert response.content == b"payload"


def test_content_disposition_carries_the_public_name(client_factory,
                                                     sized_file):
    source = sized_file("internal.tmp", data=b"payload")
    client = client_factory(named_function(source, "report.pdf"))

    result = invoke(client, "send_fixed")
    response = client.get(f"/returns/{result['value']}")
    disposition = response.headers["content-disposition"]

    assert disposition.endswith('filename="report.pdf"')
    assert result["value"].removesuffix("report.pdf") not in disposition


def test_media_type_is_octet_stream(client_factory, sized_file):
    source = sized_file("report.txt", data=b"payload")
    client = client_factory(path_function(source))

    result = invoke(client, "send_file")
    response = client.get(f"/returns/{result['value']}")

    assert response.headers["content-type"] == "application/octet-stream"


def test_string_return_is_stored_as_a_path(client_factory, sized_file):
    source = sized_file("report.txt", data=b"from a str path")
    client = client_factory(text_function(source))

    result = invoke(client, "send_text_path")
    response = client.get(f"/returns/{result['value']}")

    assert result["filename"] == "report.txt"
    assert response.content == b"from a str path"


def test_bytes_return_is_stored_with_its_name(client_factory):
    client = client_factory(bytes_function(b"generated", "memory.pdf"))

    result = invoke(client, "send_bytes")
    response = client.get(f"/returns/{result['value']}")

    assert result["filename"] == "memory.pdf"
    assert response.content == b"generated"


def test_unknown_reference_answers_404(client_factory, sized_file):
    source = sized_file("report.txt", data=b"payload")
    client = client_factory(path_function(source))

    assert client.get("/returns/deadbeef.report.txt").status_code == 404


@pytest.mark.parametrize("reference", TRAVERSALS)
def test_traversal_answers_404(client_factory, sized_file, reference):
    source = sized_file("report.txt", data=b"payload")
    client = client_factory(path_function(source))

    assert client.get(f"/returns/{reference}").status_code == 404


def test_returns_route_is_absent_without_declared_downloads(client_factory):
    client = client_factory(plain_function)

    assert client.get("/returns/anything.txt").status_code == 404


def test_returning_a_file_does_not_expose_an_arbitrary_path(client_factory,
                                                            sized_file):
    secret = sized_file("secret.txt", data=b"top secret")
    source = sized_file("report.txt", data=b"payload")
    client = client_factory(path_function(source))
    allowed = invoke(client, "send_file")["value"]

    assert client.get(f"/returns/{allowed}").content == b"payload"

    attempts = [
        "secret.txt",
        str(secret),
        str(secret).replace("\\", "/"),
        f"../{secret.name}",
        f"..\\{secret.name}",
        "%2e%2e%2fsecret.txt",
    ]

    for attempt in attempts:
        response = client.get(f"/returns/{attempt}")

        assert response.status_code == 404
        assert b"top secret" not in response.content


def test_returned_file_is_a_copy_inside_the_returns_directory(client_factory,
                                                             sized_file,
                                                             returns_dir):
    source = sized_file("report.txt", data=b"payload")
    client = client_factory(path_function(source))

    reference = invoke(client, "send_file")["value"]

    assert (returns_dir / reference).is_file()
    assert [path.name for path in returns_dir.iterdir()] == [reference]


def test_returns_directory_of_the_test_is_respected(client_factory,
                                                    sized_file, returns_dir):
    source = sized_file("report.txt", data=b"payload")
    client = client_factory(path_function(source))

    reference = invoke(client, "send_file")["value"]
    served, _ = stored_return(reference)

    assert served.parent == returns_dir


def test_awkward_filename_is_encoded_in_the_header(client_factory, sized_file):
    source = sized_file("internal.tmp", data=b"payload")
    client = client_factory(named_function(source, "a b;c=d.txt"))

    result = invoke(client, "send_fixed")
    response = client.get(f"/returns/{result['value']}")

    assert response.status_code == 200
    assert response.content == b"payload"
    assert "\r" not in response.headers["content-disposition"]
    assert "\n" not in response.headers["content-disposition"]


def test_awkward_filename_keeps_its_public_name(client_factory, sized_file):
    source = sized_file("internal.tmp", data=b"payload")
    client = client_factory(named_function(source, "a b;c=d.txt"))

    result = invoke(client, "send_fixed")

    assert result["filename"] == "a b;c=d.txt"
    assert stored_return(result["value"])[1] == "a b;c=d.txt"


@pytest.mark.parametrize("filename", ['a"b.txt', "NUL", "report.txt ",
                                      "r" * (RETURN_LIMIT + 1)])
def test_a_filename_the_route_would_refuse_is_never_written(client_factory,
                                                            sized_file,
                                                            returns_dir,
                                                            filename):
    source = sized_file("internal.tmp", data=b"payload")
    client = client_factory(named_function(source, filename))

    response = client.post("/send_fixed/invoke", json={"times": 1})

    assert response.status_code == 500
    assert response.json()["error"].startswith(
        "ReturnContractError: Download filename: "
    )
    assert list(returns_dir.iterdir()) == []


def test_a_refused_filename_reports_no_local_path(client_factory, sized_file,
                                                  returns_dir):
    source = sized_file("internal.tmp", data=b"payload")
    client = client_factory(named_function(source, 'a"b.txt'))

    response = client.post("/send_fixed/invoke", json={"times": 1})

    assert not carries(response.json()["error"], source)
    assert not carries(response.json()["error"], source.parent)
    assert not carries(response.json()["error"], returns_dir)


def test_several_downloads_keep_their_order(client_factory, sized_file):
    first = sized_file("first.txt", data=b"1")
    second = sized_file("second.txt", data=b"2")

    def send_many(times: int = 1) -> tuple[str,
                                           Annotated[list[Path], Download()]]:
        return "Finished", [first, second]

    client = client_factory(send_many)
    outputs = invoke(client, "send_many")

    assert [output["type"] for output in outputs] == ["text", "download",
                                                      "download"]
    assert [output["filename"] for output in outputs[1:]] == ["first.txt",
                                                              "second.txt"]
