import os
import re
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import func_to_web.web.upload as upload_module
from func_to_web import app_of
from func_to_web.web.pending import parsed, pending_of, stamps_of
from func_to_web.web.references import (
    NAME_LIMIT,
    PARTIAL_SUFFIX,
    PENDING_PREFIX,
    REFERENCE_LIMIT,
    segment_of,
)
from func_to_web.web.upload import CONFLICT, PUBLISH_ATTEMPTS, checked_limit

PART_PATTERN = re.compile(r"^(?P<target>.+)\.[0-9a-f]{32}\.part$")

UNSTORABLE_REFERENCES = [
    "~pfile.txt",
    "~p0000000001~a.txt",
    "a<b.txt",
    "a>b.txt",
    'a"b.txt',
    "a|b.txt",
    "a?b.txt",
    "a*b.txt",
    "a:b.txt",
    "a.txt:evil",
    "a\x01b.txt",
    "a\x1fb.txt",
    "a\x00b.txt",
    "NUL",
    "nul.txt",
    "CON",
    "com1.log",
    "LPT9",
    "...",
    "a.",
    "a ",
    "a" * (REFERENCE_LIMIT + 1),
]

INVALID_REFERENCES = [
    "",
    ".",
    "..",
    "../evil.txt",
    "..\\evil.txt",
    "a/b.txt",
    "a\\b.txt",
    "sub/x.txt",
    "/etc/passwd",
    "C:\\x",
    "C:/x",
]


def names_in(directory):
    """What is stored, by reference: the pending prefix is not part of it."""
    names = []

    for entry in directory.iterdir():
        found = parsed(entry.name)
        names.append(entry.name if found is None else found[1])

    return sorted(names)


def raw_names_in(directory):
    return sorted(entry.name for entry in directory.iterdir())


def published(directory, reference):
    """The file a reference names on disk, promoted or still pending."""
    target = directory / reference

    if target.exists():
        return target

    stamps = stamps_of(directory, reference)

    return target if not stamps else directory / pending_of(reference,
                                                            stamps[0])


def parts_in(directory):
    return [name for name in names_in(directory) if name.endswith(".part")]


def send(client, reference, content=b"data", headers=None):
    merged = {} if headers is None else dict(headers)

    if reference is not None:
        merged["X-File-Reference"] = reference

    return client.post("/upload", content=content, headers=merged)


class ReplaceRecorder:
    def __init__(self):
        self.calls = []

    def replace(self, source, destination):
        origin = Path(source)
        target = Path(destination)

        self.calls.append({
            "source": origin.name,
            "target": target.name,
            "source_bytes": origin.read_bytes(),
            "target_existed": target.exists(),
            "target_bytes": target.read_bytes() if target.exists() else None,
        })

        os.replace(source, destination)


class FlakyReplace:

    def __init__(self, failures):
        self.failures = failures
        self.attempts = 0

    def replace(self, source, destination):
        self.attempts += 1

        if self.attempts <= self.failures:
            raise PermissionError(5, "Access is denied")

        os.replace(source, destination)


@pytest.fixture
def uploader_client(client_factory, file_function):
    return client_factory(file_function)


@pytest.fixture
def limited_client(client_factory, file_function):
    def make(limit):
        return client_factory(file_function, max_upload_bytes=limit)

    return make


@pytest.fixture
def tolerant_client(app_factory, file_function):
    clients = []

    def make(**options):
        client = TestClient(app_factory(file_function, **options),
                            raise_server_exceptions=False)
        clients.append(client)
        return client

    yield make

    for client in clients:
        client.close()


def test_checked_limit_accepts_none():
    assert checked_limit(None) is None


@pytest.mark.parametrize("value", [1, 7, 1024, 50 * 1024 * 1024])
def test_checked_limit_accepts_positive_int(value):
    assert checked_limit(value) == value


@pytest.mark.parametrize("value", [True, False])
def test_checked_limit_rejects_bool(value):
    with pytest.raises(TypeError, match="int or None"):
        checked_limit(value)


def test_checked_limit_rejects_zero():
    with pytest.raises(ValueError, match="greater than zero"):
        checked_limit(0)


@pytest.mark.parametrize("value", [-1, -1024])
def test_checked_limit_rejects_negative(value):
    with pytest.raises(ValueError, match="greater than zero"):
        checked_limit(value)


@pytest.mark.parametrize("value", [1.0, 2.5, float("inf")])
def test_checked_limit_rejects_float(value):
    with pytest.raises(TypeError, match="int or None"):
        checked_limit(value)


@pytest.mark.parametrize("value", ["10", "", "1024"])
def test_checked_limit_rejects_str(value):
    with pytest.raises(TypeError, match="int or None"):
        checked_limit(value)


def test_router_accepts_no_limit(file_function):
    assert app_of(file_function, max_upload_bytes=None) is not None


def test_router_accepts_positive_limit(file_function):
    assert app_of(file_function, max_upload_bytes=4096) is not None


@pytest.mark.parametrize("value", [True, False, 1.0, "10", b"10"])
def test_router_rejects_non_int_limit(file_function, value):
    with pytest.raises(TypeError, match="int or None"):
        app_of(file_function, max_upload_bytes=value)


@pytest.mark.parametrize("value", [0, -1])
def test_router_rejects_non_positive_limit(file_function, value):
    with pytest.raises(ValueError, match="greater than zero"):
        app_of(file_function, max_upload_bytes=value)


def test_valid_reference_is_accepted(uploader_client, uploads_dir):
    response = send(uploader_client, "report-0123abcd.txt", b"body")

    assert response.status_code == 200
    assert response.json() == {"uploaded": True}
    assert published(uploads_dir, "report-0123abcd.txt").read_bytes() == b"body"


@pytest.mark.parametrize("reference", INVALID_REFERENCES)
def test_invalid_reference_is_refused(uploader_client, uploads_dir, reference):
    response = send(uploader_client, reference)

    assert response.status_code == 400
    assert response.json()["detail"].startswith("X-File-Reference ")
    assert names_in(uploads_dir) == []


@pytest.mark.parametrize("reference", ["../evil.txt", "..\\evil.txt"])
def test_traversal_reference_never_escapes(uploader_client, uploads_dir,
                                           reference):
    response = send(uploader_client, reference)

    assert response.status_code == 400
    assert names_in(uploads_dir) == []
    assert not (uploads_dir.parent / "evil.txt").exists()


def test_missing_reference_header_is_refused(uploader_client, uploads_dir):
    response = send(uploader_client, None)

    assert response.status_code == 400
    assert response.json() == {"detail": "X-File-Reference must be a file name"}
    assert names_in(uploads_dir) == []


def test_unknown_reference_is_still_stored(uploader_client, uploads_dir):
    response = send(uploader_client, "never-seen-9999.txt", b"body")

    assert response.status_code == 200
    assert names_in(uploads_dir) == ["never-seen-9999.txt"]


def test_unicode_reference_is_accepted(uploader_client, uploads_dir):
    response = uploader_client.post(
        "/upload",
        content=b"body",
        headers={"X-File-Reference": "informe.txt".encode()},
    )

    assert response.status_code == 200
    assert names_in(uploads_dir) == ["informe.txt"]


def test_non_ascii_reference_header_is_a_transport_error(uploader_client):
    with pytest.raises(UnicodeEncodeError):
        send(uploader_client, "informe-ñ.txt")


def test_repeated_reference_header_uses_the_first_value(uploader_client,
                                                        uploads_dir):
    response = uploader_client.post(
        "/upload",
        content=b"body",
        headers=[("X-File-Reference", "first.txt"),
                 ("X-File-Reference", "second.txt")],
    )

    assert response.status_code == 200
    assert names_in(uploads_dir) == ["first.txt"]


def test_overlong_reference_is_refused_without_a_server_error(tolerant_client,
                                                              uploads_dir):
    client = tolerant_client()

    response = send(client, "a" * 300 + ".txt")

    assert response.status_code != 500
    assert parts_in(uploads_dir) == []


def test_null_byte_reference_is_refused_without_a_server_error(tolerant_client,
                                                               uploads_dir):
    client = tolerant_client()

    response = send(client, "a\x00b.txt")

    assert response.status_code != 500
    assert parts_in(uploads_dir) == []


def test_no_invalid_reference_ever_yields_a_server_error(tolerant_client):
    client = tolerant_client()

    codes = {reference: send(client, reference).status_code
             for reference in INVALID_REFERENCES}

    assert 500 not in codes.values()


def test_empty_body_is_stored_as_an_empty_file(uploader_client, uploads_dir):
    response = send(uploader_client, "empty.txt", b"")

    assert response.status_code == 200
    assert published(uploads_dir, "empty.txt").read_bytes() == b""


def test_single_byte_body_is_stored(uploader_client, uploads_dir):
    response = send(uploader_client, "one.txt", b"x")

    assert response.status_code == 200
    assert published(uploads_dir, "one.txt").read_bytes() == b"x"


@pytest.mark.parametrize("limit", [1, 4, 1024])
def test_body_of_exactly_the_limit_is_accepted(limited_client, uploads_dir,
                                               limit):
    client = limited_client(limit)

    response = send(client, "exact.txt", b"x" * limit)

    assert response.status_code == 200
    assert published(uploads_dir, "exact.txt").stat().st_size == limit


@pytest.mark.parametrize("limit", [1, 4, 1024])
def test_one_byte_over_the_limit_is_refused(limited_client, uploads_dir, limit):
    client = limited_client(limit)

    response = send(client, "over.txt", b"x" * (limit + 1))

    assert response.status_code == 413
    assert names_in(uploads_dir) == []


def test_streamed_body_over_the_limit_is_refused(limited_client, uploads_dir):
    client = limited_client(4)

    response = send(client, "over.txt", iter([b"xx", b"xx", b"xx"]))

    assert response.status_code == 413
    assert names_in(uploads_dir) == []


def test_body_arriving_in_several_chunks_is_joined(uploader_client,
                                                   uploads_dir):
    response = send(uploader_client, "chunks.txt",
                    iter([b"ab", b"", b"cd", b"ef"]))

    assert response.status_code == 200
    assert published(uploads_dir, "chunks.txt").read_bytes() == b"abcdef"


def test_exact_content_length_is_accepted(limited_client, uploads_dir):
    client = limited_client(8)

    response = send(client, "declared.txt", iter([b"xxxx"]),
                    headers={"Content-Length": "4"})

    assert response.status_code == 200
    assert published(uploads_dir, "declared.txt").read_bytes() == b"xxxx"


def test_content_length_equal_to_the_limit_is_accepted(limited_client,
                                                       uploads_dir):
    client = limited_client(4)

    response = send(client, "edge.txt", iter([b"xxxx"]),
                    headers={"Content-Length": "4"})

    assert response.status_code == 200
    assert published(uploads_dir, "edge.txt").read_bytes() == b"xxxx"


def test_content_length_over_the_limit_is_refused_before_writing(
        limited_client, uploads_dir):
    client = limited_client(4)

    response = send(client, "declared.txt", iter([b"xx"]),
                    headers={"Content-Length": "999"})

    assert response.status_code == 413
    assert names_in(uploads_dir) == []


def test_content_length_smaller_than_the_body_does_not_truncate(
        uploader_client, uploads_dir):
    response = send(uploader_client, "lying.txt", b"xxxx",
                    headers={"Content-Length": "2"})

    assert response.status_code == 200
    assert published(uploads_dir, "lying.txt").read_bytes() == b"xxxx"


def test_content_length_smaller_than_the_body_still_hits_the_limit(
        limited_client, uploads_dir):
    client = limited_client(4)

    response = send(client, "lying.txt", b"x" * 6,
                    headers={"Content-Length": "2"})

    assert response.status_code == 413
    assert names_in(uploads_dir) == []


def test_absent_content_length_is_accepted(limited_client, uploads_dir):
    client = limited_client(8)

    response = send(client, "absent.txt", iter([b"xx", b"xx"]))

    assert response.status_code == 200
    assert published(uploads_dir, "absent.txt").read_bytes() == b"xxxx"


@pytest.mark.parametrize("declared", ["abc", "-4", "4.0", "", " 4"])
def test_non_numeric_content_length_is_ignored(limited_client, uploads_dir,
                                               declared):
    client = limited_client(8)

    response = send(client, "weird.txt", b"xxxx",
                    headers={"Content-Length": declared})

    assert response.status_code == 200
    assert published(uploads_dir, "weird.txt").read_bytes() == b"xxxx"


def test_interrupted_body_leaves_no_trace(tolerant_client, uploads_dir):
    client = tolerant_client()

    def interrupted():
        yield b"xx"
        raise RuntimeError("connection lost")

    send(client, "broken.txt", interrupted())

    assert names_in(uploads_dir) == []


def test_storage_directory_is_created_when_missing(uploader_client,
                                                   uploads_dir):
    uploads_dir.rmdir()

    response = send(uploader_client, "fresh.txt", b"body")

    assert response.status_code == 200
    assert uploads_dir.is_dir()
    assert published(uploads_dir, "fresh.txt").read_bytes() == b"body"


def test_body_is_written_to_a_partial_file(uploader_client, uploads_dir,
                                           monkeypatch):
    recorder = ReplaceRecorder()
    monkeypatch.setattr(upload_module, "os", recorder)

    response = send(uploader_client, "a.txt", b"payload")

    assert response.status_code == 200
    assert len(recorder.calls) == 1

    call = recorder.calls[0]
    match = PART_PATTERN.match(call["source"])

    assert match is not None
    assert match.group("target") == "a.txt"
    assert call["source_bytes"] == b"payload"


def test_publication_is_a_rename_onto_a_free_name(uploader_client, uploads_dir,
                                                  monkeypatch):
    send(uploader_client, "taken.txt", b"old")

    recorder = ReplaceRecorder()
    monkeypatch.setattr(upload_module, "os", recorder)

    response = send(uploader_client, "free.txt", b"new")

    assert response.status_code == 200

    call = recorder.calls[0]

    assert parsed(call["target"])[1] == "free.txt"
    assert call["target_existed"] is False
    assert call["target_bytes"] is None
    assert published(uploads_dir, "free.txt").read_bytes() == b"new"
    assert published(uploads_dir, "taken.txt").read_bytes() == b"old"


def test_partial_file_is_removed_when_the_limit_is_hit(limited_client,
                                                       uploads_dir):
    client = limited_client(4)

    send(client, "a.txt", iter([b"xx", b"xxx"]))

    assert parts_in(uploads_dir) == []
    assert names_in(uploads_dir) == []


def test_previous_file_survives_a_refused_second_upload(limited_client,
                                                        uploads_dir):
    client = limited_client(4)

    assert send(client, "a.txt", b"keep").status_code == 200
    assert send(client, "a.txt", b"toolong").status_code == CONFLICT

    assert published(uploads_dir, "a.txt").read_bytes() == b"keep"
    assert names_in(uploads_dir) == ["a.txt"]


def test_a_second_upload_never_substitutes_the_content(uploader_client,
                                                       uploads_dir):
    send(uploader_client, "a.txt", b"first")
    second = send(uploader_client, "a.txt", b"second-and-longer")

    assert second.status_code == CONFLICT
    assert published(uploads_dir, "a.txt").read_bytes() == b"first"
    assert names_in(uploads_dir) == ["a.txt"]


def test_no_residue_survives_any_kind_of_failure(tolerant_client, uploads_dir):
    client = tolerant_client(max_upload_bytes=4)

    def interrupted():
        yield b"xx"
        raise RuntimeError("connection lost")

    send(client, "../evil.txt")
    send(client, "", b"x")
    send(client, None, b"x")
    send(client, "big.txt", b"x" * 40)
    send(client, "big.txt", iter([b"xx", b"xxx"]))
    send(client, "cut.txt", interrupted())

    assert names_in(uploads_dir) == []


def test_two_references_coexist(uploader_client, uploads_dir):
    send(uploader_client, "a.txt", b"one")
    send(uploader_client, "b.txt", b"two")

    assert names_in(uploads_dir) == ["a.txt", "b.txt"]
    assert published(uploads_dir, "a.txt").read_bytes() == b"one"
    assert published(uploads_dir, "b.txt").read_bytes() == b"two"


def test_same_reference_uploaded_twice_keeps_the_first_file(uploader_client,
                                                            uploads_dir):
    first = send(uploader_client, "a.txt", b"one")
    second = send(uploader_client, "a.txt", b"two")

    assert (first.status_code, second.status_code) == (200, CONFLICT)
    assert names_in(uploads_dir) == ["a.txt"]
    assert published(uploads_dir, "a.txt").read_bytes() == b"one"


def test_a_published_reference_is_refused_with_its_own_message(uploader_client):
    send(uploader_client, "a.txt", b"one")

    response = send(uploader_client, "a.txt", b"two")

    assert response.status_code == CONFLICT
    assert response.json() == {
        "detail": "a file with this reference already exists"
    }


def test_a_refused_second_upload_leaves_no_partial(uploader_client,
                                                   uploads_dir):
    send(uploader_client, "a.txt", b"one")

    assert send(uploader_client, "a.txt", b"two").status_code == CONFLICT
    assert parts_in(uploads_dir) == []
    assert names_in(uploads_dir) == ["a.txt"]


def test_a_file_stored_outside_the_endpoint_is_also_protected(uploader_client,
                                                              stored_file,
                                                              uploads_dir):
    stored_file("planted.txt", data=b"planted")

    response = send(uploader_client, "planted.txt", b"other")

    assert response.status_code == CONFLICT
    assert published(uploads_dir, "planted.txt").read_bytes() == b"planted"


def test_an_upload_that_failed_before_publishing_can_be_retried(
        limited_client, uploads_dir):
    client = limited_client(4)

    refused = send(client, "a.txt", b"toolong")

    assert refused.status_code == 413
    assert names_in(uploads_dir) == []

    retried = send(client, "a.txt", b"ok")

    assert retried.status_code == 200
    assert published(uploads_dir, "a.txt").read_bytes() == b"ok"


@pytest.mark.parametrize("reference", ["../a.txt", "sub/a.txt", ".."])
def test_a_malformed_reference_is_still_a_400_not_a_conflict(uploader_client,
                                                             stored_file,
                                                             reference):
    stored_file("a.txt", data=b"stored")

    response = send(uploader_client, reference, b"other")

    assert response.status_code == 400
    assert response.json()["detail"].startswith("X-File-Reference ")


def test_success_body_is_exactly_the_uploaded_flag(uploader_client):
    response = send(uploader_client, "a.txt", b"x")

    assert response.status_code == 200
    assert response.json() == {"uploaded": True}


def test_too_large_message_names_the_limit(limited_client):
    client = limited_client(7)

    response = send(client, "a.txt", b"x" * 8)

    assert response.status_code == 413
    assert response.json() == {
        "detail": "uploaded file exceeds the maximum size of 7 bytes"
    }


def test_streamed_and_declared_rejections_share_one_message(limited_client):
    client = limited_client(4)

    declared = send(client, "a.txt", iter([b"xx"]),
                    headers={"Content-Length": "99"})
    streamed = send(client, "a.txt", iter([b"xx", b"xxx"]))

    assert declared.json() == streamed.json()


def test_no_limit_accepts_a_large_body(uploader_client, uploads_dir):
    response = send(uploader_client, "a.txt", b"x" * 200_000)

    assert response.status_code == 200
    assert published(uploads_dir, "a.txt").stat().st_size == 200_000


def test_upload_route_is_absent_without_file_fields(client_factory, scalar):
    client = client_factory(scalar)

    response = client.post("/upload", content=b"x",
                           headers={"X-File-Reference": "a.txt"})

    assert response.status_code == 404


def test_upload_route_follows_the_router_prefix(client_factory, file_function,
                                                uploads_dir):
    client = client_factory(file_function, prefix="/tools")

    response = client.post("/tools/upload", content=b"body",
                           headers={"X-File-Reference": "a.txt"})

    assert response.status_code == 200
    assert published(uploads_dir, "a.txt").read_bytes() == b"body"


@pytest.mark.parametrize("failures", range(PUBLISH_ATTEMPTS))
def test_a_transient_publication_failure_is_retried(uploader_client,
                                                    uploads_dir, monkeypatch,
                                                    failures):
    flaky = FlakyReplace(failures)
    monkeypatch.setattr(upload_module, "os", flaky)

    response = send(uploader_client, "a.txt", b"body")

    assert response.status_code == 200
    assert flaky.attempts == failures + 1
    assert published(uploads_dir, "a.txt").read_bytes() == b"body"
    assert parts_in(uploads_dir) == []


def test_publication_retries_several_times_before_giving_up(uploader_client,
                                                            uploads_dir,
                                                            monkeypatch):
    flaky = FlakyReplace(3)

    monkeypatch.setattr(upload_module, "os", flaky)

    response = send(uploader_client, "a.txt", b"body")

    assert response.status_code == 200
    assert flaky.attempts == 4
    assert published(uploads_dir, "a.txt").read_bytes() == b"body"


def test_publication_gives_up_after_the_last_attempt(tolerant_client,
                                                     uploads_dir, monkeypatch):
    flaky = FlakyReplace(PUBLISH_ATTEMPTS)
    monkeypatch.setattr(upload_module, "os", flaky)

    response = send(tolerant_client(), "a.txt", b"body")

    assert response.status_code == 500
    assert flaky.attempts == PUBLISH_ATTEMPTS


def test_a_server_side_publication_failure_is_a_500_not_a_400(
        tolerant_client, uploads_dir, monkeypatch):
    class Denied:
        def replace(self, source, destination):
            raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(upload_module, "os", Denied())

    response = send(tolerant_client(), "a.txt", b"body")

    assert response.status_code == 500


def test_a_failed_publication_leaves_no_residue(tolerant_client, uploads_dir,
                                                monkeypatch):
    monkeypatch.setattr(upload_module, "os",
                        FlakyReplace(PUBLISH_ATTEMPTS))

    send(tolerant_client(), "a.txt", b"body")

    assert names_in(uploads_dir) == []


def test_a_failed_publication_keeps_what_is_already_stored(tolerant_client,
                                                           uploads_dir,
                                                           monkeypatch):
    client = tolerant_client()

    assert send(client, "a.txt", b"keep").status_code == 200

    monkeypatch.setattr(upload_module, "os", FlakyReplace(PUBLISH_ATTEMPTS))

    assert send(client, "b.txt", b"new").status_code == 500

    monkeypatch.undo()

    assert names_in(uploads_dir) == ["a.txt"]
    assert published(uploads_dir, "a.txt").read_bytes() == b"keep"


def test_a_failing_cleanup_does_not_mask_the_original_failure(tolerant_client,
                                                              uploads_dir,
                                                              monkeypatch):
    monkeypatch.setattr(upload_module, "os", FlakyReplace(PUBLISH_ATTEMPTS))

    def refuse(self, missing_ok=False):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(Path, "unlink", refuse)

    response = send(tolerant_client(), "a.txt", b"body")

    assert response.status_code == 500


@pytest.mark.parametrize("reference", UNSTORABLE_REFERENCES)
def test_a_reference_the_filesystem_cannot_store_is_refused_with_400(
        tolerant_client, uploads_dir, reference):
    client = tolerant_client()

    response = send(client, reference)

    assert response.status_code == 400
    assert response.json()["detail"].startswith("X-File-Reference ")
    assert names_in(uploads_dir) == []


def test_the_reference_limit_is_derived_from_what_publishing_adds():
    assert PARTIAL_SUFFIX == len(f".{uuid4().hex}.part")
    assert PENDING_PREFIX == len(pending_of("", 0))
    assert REFERENCE_LIMIT == NAME_LIMIT - PARTIAL_SUFFIX - PENDING_PREFIX


def test_a_reference_of_exactly_the_limit_is_stored(uploader_client,
                                                    uploads_dir):
    reference = "a" * (REFERENCE_LIMIT - 4) + ".txt"

    response = send(uploader_client, reference, b"body")

    assert response.status_code == 200
    assert published(uploads_dir, reference).read_bytes() == b"body"


def test_one_byte_over_the_limit_names_the_computed_limit(tolerant_client,
                                                          uploads_dir):
    client = tolerant_client()

    response = send(client, "a" * (REFERENCE_LIMIT + 1))

    assert response.status_code == 400
    assert response.json()["detail"] == (
        f"X-File-Reference is longer than {REFERENCE_LIMIT} bytes"
    )
    assert names_in(uploads_dir) == []


def test_the_limit_counts_utf8_bytes_not_characters():
    reference = "ñ" * (REFERENCE_LIMIT // 2 + 1)

    assert len(reference) < REFERENCE_LIMIT
    assert len(reference.encode("utf-8")) > REFERENCE_LIMIT

    with pytest.raises(ValueError, match=f"longer than {REFERENCE_LIMIT}"):
        segment_of(reference)


def test_a_partial_of_the_longest_reference_fits_the_name_limit(uploads_dir):
    reference = segment_of("a" * REFERENCE_LIMIT)
    partial = uploads_dir / f"{reference}.{uuid4().hex}.part"

    assert len(partial.name.encode("utf-8")) == NAME_LIMIT - PENDING_PREFIX

    partial.write_bytes(b"x")

    assert partial.is_file()


def test_a_pending_of_the_longest_reference_fits_the_name_limit(uploads_dir):
    reference = segment_of("a" * REFERENCE_LIMIT)
    target = uploads_dir / pending_of(reference, 9999999999)

    assert len(target.name.encode("utf-8")) == NAME_LIMIT - PARTIAL_SUFFIX

    target.write_bytes(b"x")

    assert target.is_file()


def test_uploaded_file_is_reachable_by_the_function(client_factory,
                                                    file_function):
    client = client_factory(file_function)

    assert send(client, "a.txt", b"hello").status_code == 200

    response = client.post("/read/invoke", json={"document": "a.txt"})

    assert response.status_code == 200
    assert response.json()["result"]["value"] == "hello"
