import json
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import pytest

from shared import carries
from func_to_web import FileHint

TxtFile = Annotated[str, FileHint(extensions=(".txt",))]
AnyFile = Annotated[str, FileHint()]
GzFile = Annotated[str, FileHint(extensions=(".gz",))]
TarGzFile = Annotated[str, FileHint(extensions=(".tar.gz",))]

CEILING = 200
MINIMUM = 50
MAXIMUM = 120

BoundedFile = Annotated[
    str,
    FileHint(extensions=(".txt",), min_size=MINIMUM, max_size=MAXIMUM),
]

RECEIVED: list[str] = []


@pytest.fixture(autouse=True)
def clear_received():
    RECEIVED.clear()
    yield
    RECEIVED.clear()


def read_stored(path):
    RECEIVED.append(path)
    return Path(path).read_text(encoding="utf-8")


@dataclass
class Attachment:
    document: TxtFile
    tag: str = "t"


@dataclass
class BoundedAttachment:
    document: BoundedFile
    tag: str = "t"


def read_one(document: TxtFile) -> str:
    """Reads one file."""
    return read_stored(document)


def read_optional(document: TxtFile | None = None) -> str:
    """Reads an optional file."""
    return "none" if document is None else read_stored(document)


def read_many(documents: list[TxtFile]) -> str:
    """Reads a list of files."""
    return "|".join(read_stored(item) for item in documents)


def read_optional_items(documents: list[TxtFile | None]) -> str:
    """Reads a list of optional files."""
    return "|".join("none" if item is None else read_stored(item)
                    for item in documents)


def read_mixed_items(items: list[TxtFile | int]) -> str:
    """Reads a list of files or numbers."""
    return "|".join(str(item) if type(item) is int else read_stored(item)
                    for item in items)


def read_groups(groups: list[list[TxtFile]]) -> str:
    """Reads groups of files."""
    return "|".join(",".join(read_stored(item) for item in group)
                    for group in groups)


def read_attachment(item: Attachment) -> str:
    """Reads a dataclass carrying a file."""
    return f"{item.tag}:{read_stored(item.document)}"


def read_attachments(items: list[Attachment]) -> str:
    """Reads dataclasses carrying files."""
    return "|".join(f"{item.tag}:{read_stored(item.document)}"
                    for item in items)


def read_either(item: TxtFile | int) -> str:
    """Reads a file or a number."""
    return str(item) if type(item) is int else read_stored(item)


def read_several(first: TxtFile, second: TxtFile, extra: list[TxtFile]) -> str:
    """Reads several files at once."""
    return "|".join([read_stored(first), read_stored(second),
                     *(read_stored(item) for item in extra)])


def scale_report(document: TxtFile, factor: int = 1) -> str:
    """Repeats a stored file."""
    return read_stored(document) * factor


def read_bounded(document: BoundedFile) -> str:
    """Reads a size bounded file."""
    return read_stored(document)


def read_bounded_list(documents: list[BoundedFile]) -> str:
    """Reads size bounded files."""
    return "|".join(read_stored(item) for item in documents)


def read_bounded_attachment(item: BoundedAttachment) -> str:
    """Reads a dataclass with a size bounded file."""
    return read_stored(item.document)


def read_bounded_either(item: BoundedFile | int) -> str:
    """Reads a size bounded file or a number."""
    return str(item) if type(item) is int else read_stored(item)


def read_any(document: AnyFile) -> str:
    """Reads any file."""
    return read_stored(document)


def read_gz(document: GzFile) -> str:
    """Reads a gz file."""
    return read_stored(document)


def read_tar_gz(document: TarGzFile) -> str:
    """Reads a tar.gz file."""
    return read_stored(document)


def upload(client, reference, payload, prefix=""):
    return client.post(
        f"{prefix}/upload",
        content=payload,
        headers={"X-File-Reference": reference},
    )


def put(client, reference, text, prefix=""):
    response = upload(client, reference, text.encode("utf-8"), prefix=prefix)

    assert response.status_code == 200

    return reference


def put_bytes(client, reference, size, prefix=""):
    response = upload(client, reference, b"x" * size, prefix=prefix)

    assert response.status_code == 200

    return reference


def invoke(client, slug, payload, prefix=""):
    return client.post(f"{prefix}/{slug}/invoke", json=payload)


def text_of(response):
    assert response.status_code == 200

    return response.json()["result"]["value"]


def error_of(response):
    return response.json()["error"]


def assert_real_paths(uploads_dir):
    assert RECEIVED

    for path in RECEIVED:
        assert Path(path).is_file()
        assert Path(path).parent == uploads_dir.resolve()


def file_options_in(node):
    """The options of the first file node under node, however it is wrapped."""
    if node.get("kind") == "file":
        return node["options"]

    children = [child for child in (node.get("item"), node.get("node"))
                if child is not None]
    children += [field["node"] for field in node.get("fields", ())]
    children += [branch["node"] for branch in node.get("branches", ())]

    for child in children:
        found = file_options_in(child)

        if found is not None:
            return found

    return None


def served_file_options(client, slug, name, plan_of_page):
    page = client.get(f"/{slug}/")

    assert page.status_code == 200

    plan = plan_of_page(page.text)
    field = next(item for item in plan["fields"] if item["name"] == name)

    return file_options_in(field["node"])


def test_a_rejected_extension_names_the_file_not_its_path(client_factory,
                                                          uploads_dir):
    client = client_factory(read_one)
    reference = put(client, "ext-9.md", "nope")

    response = invoke(client, "read_one", {"document": reference})

    assert response.status_code == 422
    assert f"not an accepted file type: {reference!r}" in error_of(response)
    assert not carries(response.text, uploads_dir)


def test_a_rejected_prefill_names_the_file_not_its_path(client_factory,
                                                        uploads_dir):
    client = client_factory(read_one)
    reference = put(client, "ext-10.md", "nope")

    response = client.get(
        "/read_one/", params={"prefill": json.dumps({"document": reference})})

    assert response.status_code == 400
    assert f"not an accepted file type: {reference!r}" in (
        response.json()["detail"])
    assert not carries(response.text, uploads_dir)


def test_a_rejected_extension_over_the_stream_names_no_path(client_factory,
                                                            uploads_dir):
    client = client_factory(read_one)
    reference = put(client, "ext-11.md", "nope")

    response = client.post("/read_one/invoke-stream",
                           json={"document": reference})

    assert f"not an accepted file type: {reference!r}" in response.text
    assert not carries(response.text, uploads_dir)


def test_single_file_round_trip(client_factory, uploads_dir):
    client = client_factory(read_one)
    reference = put(client, "alpha-1.txt", "alpha")

    response = invoke(client, "read_one", {"document": reference})

    assert text_of(response) == "alpha"
    assert_real_paths(uploads_dir)


def test_function_receives_the_stored_path_not_the_reference(client_factory,
                                                             uploads_dir):
    client = client_factory(read_one)
    reference = put(client, "beta-1.txt", "beta")

    invoke(client, "read_one", {"document": reference})

    assert RECEIVED == [str(uploads_dir.resolve() / reference)]
    assert Path(RECEIVED[0]).read_bytes() == b"beta"


def test_optional_file_with_a_value(client_factory, uploads_dir):
    client = client_factory(read_optional)
    reference = put(client, "gamma-1.txt", "gamma")

    response = invoke(client, "read_optional", {"document": reference})

    assert text_of(response) == "gamma"
    assert_real_paths(uploads_dir)


def test_optional_file_with_none(client_factory):
    client = client_factory(read_optional)

    response = invoke(client, "read_optional", {"document": None})

    assert text_of(response) == "none"
    assert RECEIVED == []


def test_optional_file_omitted_takes_its_default(client_factory):
    client = client_factory(read_optional)

    response = invoke(client, "read_optional", {})

    assert text_of(response) == "none"


def test_list_of_files(client_factory, uploads_dir):
    client = client_factory(read_many)
    first = put(client, "one-1.txt", "one")
    second = put(client, "two-1.txt", "two")

    response = invoke(client, "read_many", {"documents": [first, second]})

    assert text_of(response) == "one|two"
    assert_real_paths(uploads_dir)


def test_list_preserves_the_declared_order(client_factory):
    client = client_factory(read_many)
    first = put(client, "a-1.txt", "a")
    second = put(client, "b-1.txt", "b")
    third = put(client, "c-1.txt", "c")

    forward = invoke(client, "read_many",
                     {"documents": [first, second, third]})

    assert text_of(forward) == "a|b|c"

    backward = invoke(client, "read_many",
                      {"documents": [third, second, first]})

    assert text_of(backward) == "c|b|a"


def test_list_of_optional_files(client_factory, uploads_dir):
    client = client_factory(read_optional_items)
    first = put(client, "opt-1.txt", "first")
    second = put(client, "opt-2.txt", "second")

    response = invoke(client, "read_optional_items",
                      {"documents": [first, None, second]})

    assert text_of(response) == "first|none|second"
    assert_real_paths(uploads_dir)


def test_list_of_file_or_int(client_factory, uploads_dir):
    client = client_factory(read_mixed_items)
    reference = put(client, "mixed-1.txt", "doc")

    response = invoke(client, "read_mixed_items",
                      {"items": [reference, 7, reference]})

    assert text_of(response) == "doc|7|doc"
    assert_real_paths(uploads_dir)


def test_list_of_lists_of_files(client_factory, uploads_dir):
    client = client_factory(read_groups)
    first = put(client, "g-1.txt", "g1")
    second = put(client, "g-2.txt", "g2")
    third = put(client, "g-3.txt", "g3")

    response = invoke(client, "read_groups",
                      {"groups": [[first, second], [third]]})

    assert text_of(response) == "g1,g2|g3"
    assert_real_paths(uploads_dir)


def test_dataclass_carrying_a_file(client_factory, uploads_dir):
    client = client_factory(read_attachment)
    reference = put(client, "att-1.txt", "body")

    response = invoke(client, "read_attachment",
                      {"item": {"document": reference, "tag": "note"}})

    assert text_of(response) == "note:body"
    assert_real_paths(uploads_dir)


def test_list_of_dataclasses_carrying_files(client_factory, uploads_dir):
    client = client_factory(read_attachments)
    first = put(client, "att-2.txt", "one")
    second = put(client, "att-3.txt", "two")

    response = invoke(client, "read_attachments", {"items": [
        {"document": first, "tag": "x"},
        {"document": second, "tag": "y"},
    ]})

    assert text_of(response) == "x:one|y:two"
    assert_real_paths(uploads_dir)


def test_union_of_file_and_int_taking_the_file_branch(client_factory,
                                                      uploads_dir):
    client = client_factory(read_either)
    reference = put(client, "either-1.txt", "chosen")

    response = invoke(client, "read_either", {"item": reference})

    assert text_of(response) == "chosen"
    assert_real_paths(uploads_dir)


def test_union_of_file_and_int_taking_the_int_branch(client_factory):
    client = client_factory(read_either)

    response = invoke(client, "read_either", {"item": 42})

    assert text_of(response) == "42"
    assert RECEIVED == []


def test_several_files_in_one_invocation(client_factory, uploads_dir):
    client = client_factory(read_several)
    first = put(client, "many-1.txt", "1")
    second = put(client, "many-2.txt", "2")
    third = put(client, "many-3.txt", "3")
    fourth = put(client, "many-4.txt", "4")

    response = invoke(client, "read_several", {
        "first": first,
        "second": second,
        "extra": [third, fourth],
    })

    assert text_of(response) == "1|2|3|4"
    assert len(RECEIVED) == 4
    assert len(set(RECEIVED)) == 4
    assert_real_paths(uploads_dir)


def test_round_trip_under_a_router_prefix(client_factory, uploads_dir):
    client = client_factory(read_one, prefix="/tools")
    reference = put(client, "pref-1.txt", "prefixed", prefix="/tools")

    response = invoke(client, "read_one", {"document": reference},
                      prefix="/tools")

    assert text_of(response) == "prefixed"
    assert_real_paths(uploads_dir)


def test_upload_above_the_global_ceiling_is_refused(client_factory,
                                                    uploads_dir):
    client = client_factory(read_bounded, max_upload_bytes=CEILING)

    response = upload(client, "big-1.txt", b"x" * (CEILING + 1))

    assert response.status_code == 413
    assert response.json()["detail"] == (
        f"uploaded file exceeds the maximum size of {CEILING} bytes"
    )
    assert list(uploads_dir.iterdir()) == []
    assert RECEIVED == []


def test_upload_exactly_at_the_global_ceiling_is_stored(client_factory,
                                                        stored_bytes):
    client = client_factory(read_bounded, max_upload_bytes=CEILING)

    response = upload(client, "ceiling-1.txt", b"x" * CEILING)

    assert response.status_code == 200
    assert len(stored_bytes("ceiling-1.txt")) == CEILING


# Where the two byte limits live in 2.6.0.
#
# max_upload_bytes is FuncToWeb's, it counts the bytes of POST /upload as they
# arrive and answers 413. FileHint(min_size=..., max_size=...) is a rule about
# a File the visitor picks locally: pytypehintweb reads file.size in the
# browser and applies it there. Nothing measures bytes server-side any more:
# pytypehint 1.0.0 does not stat the resolved path during build(), and for a
# reference already in storage the browser has no bytes to weigh either.
#
# The tests below therefore assert the two facts that are true: the ceiling is
# enforced on the wire, and the field bounds are published in the plan so the
# browser can enforce them. They replace nine tests that asserted a 422 with
# "file too small" / "file too large" from build(); that verdict no longer
# exists at any layer, so renaming them would have kept a promise the stack
# does not make.
def test_inside_the_ceiling_but_outside_the_field_bound_still_runs(
        client_factory, stored_bytes, uploads_dir):
    client = client_factory(read_bounded, max_upload_bytes=CEILING)
    size = 150
    reference = put_bytes(client, "over-1.txt", size)

    assert len(stored_bytes(reference)) == size

    response = invoke(client, "read_bounded", {"document": reference})

    assert text_of(response) == "x" * size
    assert_real_paths(uploads_dir)


def test_file_valid_for_both_limits(client_factory, uploads_dir):
    client = client_factory(read_bounded, max_upload_bytes=CEILING)
    reference = put_bytes(client, "good-1.txt", 80)

    response = invoke(client, "read_bounded", {"document": reference})

    assert text_of(response) == "x" * 80
    assert_real_paths(uploads_dir)


def test_the_plan_publishes_the_field_size_bounds_for_the_browser(
        client_factory, plan_of_page):
    client = client_factory(read_bounded, max_upload_bytes=CEILING)

    options = served_file_options(client, "read_bounded", "document",
                                  plan_of_page)

    assert options["minSize"] == MINIMUM
    assert options["maxSize"] == MAXIMUM


def test_an_unbounded_field_publishes_no_size_bound(client_factory,
                                                    plan_of_page):
    client = client_factory(read_one)

    options = served_file_options(client, "read_one", "document", plan_of_page)

    assert options["minSize"] is None
    assert options["maxSize"] is None


def test_a_file_under_the_field_minimum_is_not_weighed_server_side(
        client_factory, uploads_dir):
    client = client_factory(read_bounded, max_upload_bytes=CEILING)
    reference = put_bytes(client, "min-under.txt", MINIMUM - 1)

    response = invoke(client, "read_bounded", {"document": reference})

    assert text_of(response) == "x" * (MINIMUM - 1)
    assert_real_paths(uploads_dir)


def test_a_file_over_the_field_maximum_is_not_weighed_server_side(
        client_factory, uploads_dir):
    client = client_factory(read_bounded, max_upload_bytes=CEILING)
    reference = put_bytes(client, "max-over.txt", MAXIMUM + 1)

    response = invoke(client, "read_bounded", {"document": reference})

    assert text_of(response) == "x" * (MAXIMUM + 1)
    assert_real_paths(uploads_dir)


def test_the_size_bound_is_published_inside_a_list(client_factory,
                                                   plan_of_page):
    client = client_factory(read_bounded_list, max_upload_bytes=CEILING)

    options = served_file_options(client, "read_bounded_list", "documents",
                                  plan_of_page)

    assert options["minSize"] == MINIMUM
    assert options["maxSize"] == MAXIMUM


def test_the_size_bound_is_published_inside_a_dataclass(client_factory,
                                                        plan_of_page):
    client = client_factory(read_bounded_attachment,
                            max_upload_bytes=CEILING)

    options = served_file_options(client, "read_bounded_attachment", "item",
                                  plan_of_page)

    assert options["minSize"] == MINIMUM
    assert options["maxSize"] == MAXIMUM


def test_the_size_bound_is_published_inside_a_union(client_factory,
                                                    plan_of_page):
    client = client_factory(read_bounded_either, max_upload_bytes=CEILING)

    options = served_file_options(client, "read_bounded_either", "item",
                                  plan_of_page)

    assert options["minSize"] == MINIMUM
    assert options["maxSize"] == MAXIMUM


# What a manual client genuinely cannot skip is FuncToWeb's storage rule: a
# reference that does not resolve raises inside decode(), so the answer is 422
# and the function is never entered. These four tests keep the shape of the
# size-verdict tests they replace, aimed at the guarantee that survived.
def test_an_unresolvable_reference_is_input_validation_not_a_server_error(
        client_factory):
    client = client_factory(read_one)

    response = invoke(client, "read_one", {"document": "ghost.txt"})

    assert response.status_code == 422
    assert error_of(response) == "FileNotFoundError: File not found: ghost.txt"
    assert "result" not in response.json()


def test_the_function_is_not_called_when_the_reference_does_not_resolve(
        client_factory):
    client = client_factory(read_one)
    good = put(client, "call-good.txt", "here")

    assert invoke(client, "read_one",
                  {"document": "call-bad.txt"}).status_code == 422
    assert RECEIVED == []

    assert invoke(client, "read_one", {"document": good}).status_code == 200
    assert len(RECEIVED) == 1


def test_a_deleted_reference_stops_the_call_even_after_a_good_one(
        client_factory, uploads_dir):
    client = client_factory(read_one)
    reference = put(client, "vanish-1.txt", "here")

    assert invoke(client, "read_one", {"document": reference}).status_code == 200

    (uploads_dir / reference).unlink()
    RECEIVED.clear()

    response = invoke(client, "read_one", {"document": reference})

    assert response.status_code == 422
    assert error_of(response) == (
        f"FileNotFoundError: File not found: {reference}")
    assert RECEIVED == []


def test_the_same_reference_verdict_arrives_over_the_stream(client_factory,
                                                            sse):
    client = client_factory(read_one)

    response = client.post("/read_one/invoke-stream",
                           json={"document": "sse-ghost.txt"})

    assert response.status_code == 200

    name, payload = sse(response.text)[-1]

    assert name == "result"
    assert payload == {
        "error": "FileNotFoundError: File not found: sse-ghost.txt"
    }
    assert RECEIVED == []


def test_the_extension_check_reaches_inside_a_list(client_factory):
    client = client_factory(read_many)
    good = put(client, "nest-good.txt", "ok")
    bad = put(client, "nest-bad.md", "nope")

    response = invoke(client, "read_many", {"documents": [good, bad]})

    assert response.status_code == 422
    assert "not an accepted file type: 'nest-bad.md'" in error_of(response)
    assert RECEIVED == []


def test_the_extension_check_reaches_inside_a_dataclass(client_factory):
    client = client_factory(read_attachment)
    bad = put(client, "nest-bad-2.md", "nope")

    response = invoke(client, "read_attachment",
                      {"item": {"document": bad, "tag": "t"}})

    assert response.status_code == 422
    assert "not an accepted file type: 'nest-bad-2.md'" in error_of(response)
    assert RECEIVED == []


def test_a_valid_file_also_flows_through_the_stream(client_factory, sse):
    client = client_factory(read_bounded, max_upload_bytes=CEILING)
    reference = put_bytes(client, "sse-good.txt", 80)

    response = client.post("/read_bounded/invoke-stream",
                           json={"document": reference})

    assert response.status_code == 200

    name, payload = sse(response.text)[-1]

    assert name == "result"
    assert payload["result"]["value"] == "x" * 80


def test_an_accepted_extension_runs(client_factory):
    client = client_factory(read_one)
    reference = put(client, "ext-1.txt", "ok")

    assert text_of(invoke(client, "read_one", {"document": reference})) == "ok"


def test_a_rejected_extension_is_unprocessable(client_factory):
    client = client_factory(read_one)
    reference = put(client, "ext-2.md", "nope")

    response = invoke(client, "read_one", {"document": reference})

    assert response.status_code == 422
    assert "not an accepted file type: 'ext-2.md'" in error_of(response)
    assert "expected one of ('.txt',)" in error_of(response)
    assert RECEIVED == []


def test_an_uppercase_reference_extension_is_accepted(client_factory,
                                                      uploads_dir):
    client = client_factory(read_one)
    reference = put(client, "ext-3.TXT", "shout")

    response = invoke(client, "read_one", {"document": reference})

    assert text_of(response) == "shout"
    assert RECEIVED[0].endswith(".TXT")
    assert_real_paths(uploads_dir)


def test_a_mixed_case_reference_extension_is_accepted(client_factory):
    client = client_factory(read_one)
    reference = put(client, "ext-4.TxT", "mixed")

    assert text_of(invoke(client, "read_one",
                          {"document": reference})) == "mixed"


def test_declared_extensions_must_be_lowercase():
    with pytest.raises(ValueError):
        FileHint(extensions=(".TXT",))


def test_a_reference_without_extension_fails_a_bound_field(client_factory):
    client = client_factory(read_one)
    reference = put(client, "bare-name", "nothing")

    response = invoke(client, "read_one", {"document": reference})

    assert response.status_code == 422
    assert "not an accepted file type" in error_of(response)


def test_a_reference_without_extension_passes_an_unbound_field(client_factory,
                                                               uploads_dir):
    client = client_factory(read_any)
    reference = put(client, "bare-name-2", "anything")

    response = invoke(client, "read_any", {"document": reference})

    assert text_of(response) == "anything"
    assert_real_paths(uploads_dir)


def test_multiple_suffixes_match_the_last_suffix(client_factory, uploads_dir):
    client = client_factory(read_gz)
    reference = put(client, "archive-1.tar.gz", "packed")

    response = invoke(client, "read_gz", {"document": reference})

    assert text_of(response) == "packed"
    assert_real_paths(uploads_dir)


def test_multiple_suffixes_match_a_compound_extension(client_factory):
    client = client_factory(read_tar_gz)
    reference = put(client, "archive-2.tar.gz", "compound")

    assert text_of(invoke(client, "read_tar_gz",
                          {"document": reference})) == "compound"


def test_a_compound_extension_rejects_a_single_suffix(client_factory):
    client = client_factory(read_tar_gz)
    reference = put(client, "archive-3.gz", "single")

    response = invoke(client, "read_tar_gz", {"document": reference})

    assert response.status_code == 422
    assert "not an accepted file type" in error_of(response)


def test_multiple_suffixes_rejected_by_an_unrelated_extension(client_factory):
    client = client_factory(read_one)
    reference = put(client, "archive-4.tar.gz", "wrong")

    response = invoke(client, "read_one", {"document": reference})

    assert response.status_code == 422
    assert "not an accepted file type" in error_of(response)


def test_a_manual_client_is_not_stopped_by_the_field_size_bound(
        client_factory, uploads_dir):
    # Stated deliberately, because it is the tempting thing to get wrong: a
    # client that skips the browser skips FileHint's byte bounds with it. The
    # only server-side limit on bytes is max_upload_bytes, and this file is
    # well inside the ceiling while being well outside the field bound.
    client = client_factory(read_bounded, max_upload_bytes=CEILING)
    reference = put_bytes(client, "manual-1.txt", MAXIMUM + 1)

    response = client.post("/read_bounded/invoke",
                           json={"document": reference})

    assert text_of(response) == "x" * (MAXIMUM + 1)
    assert_real_paths(uploads_dir)


def test_a_reference_that_never_crossed_the_upload_endpoint_has_no_bound(
        client_factory, stored_file, uploads_dir):
    # max_upload_bytes cannot speak for bytes that never reached POST /upload:
    # this file was written straight into the storage directory. It resolves
    # and runs, and no layer weighs it.
    client = client_factory(read_bounded, max_upload_bytes=CEILING)
    reference = stored_file(name="manual-2.txt", size=5)

    response = client.post("/read_bounded/invoke",
                           json={"document": reference})

    assert text_of(response) == "x" * 5
    assert_real_paths(uploads_dir)


def test_a_manual_client_with_a_valid_reference_runs(client_factory,
                                                     stored_file,
                                                     uploads_dir):
    client = client_factory(read_bounded, max_upload_bytes=CEILING)
    reference = stored_file(name="manual-3.txt", size=80)

    response = client.post("/read_bounded/invoke",
                           json={"document": reference})

    assert text_of(response) == "x" * 80
    assert_real_paths(uploads_dir)


def test_one_upload_serves_three_invocations(client_factory, uploads_dir):
    client = client_factory(scale_report)
    reference = put(client, "reuse-1.txt", "ab")

    results = [
        text_of(invoke(client, "scale_report",
                       {"document": reference, "factor": factor}))
        for factor in (1, 2, 3)
    ]

    assert results == ["ab", "abab", "ababab"]
    assert len(RECEIVED) == 3
    assert set(RECEIVED) == {str(uploads_dir.resolve() / reference)}
    assert [item.name for item in uploads_dir.iterdir()] == [reference]
