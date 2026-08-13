import os
import re
from datetime import timedelta
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import func_to_web.web.returned_files as returns_module
import func_to_web.web.upload as upload_module
from func_to_web import Download, FileHint, app_of
from func_to_web.web.pending import (
    PART_SUFFIX,
    now,
    returned_of,
    stamped_of,
)
from func_to_web.web.references import (
    FILENAME_LIMIT,
    IDENTIFIER_PREFIX,
    NAME_LIMIT,
    PARTIAL_SUFFIX,
    PENDING_MARKER,
    RETURN_LIMIT,
    RETURNS_MARKER,
    RETURNS_PREFIX,
    segment_of,
)
from func_to_web.web.returned_files import stored_return
from func_to_web.web.upload import checked_ttl

RETURNED_PATTERN = re.compile(
    r"^(?P<token>[0-9a-f]{32})\.~r(?P<stamp>\d{10})~(?P<name>.+)$"
)

RESERVED = f"cannot start with the reserved prefix '{RETURNS_MARKER}'"

TOKEN = "0" * 32

TxtFile = Annotated[str, FileHint(extensions=(".txt",))]


def naming(filename):
    def send(size: int = 4) -> Annotated[bytes, Download(filename=filename)]:
        """Returns a file."""
        return b"x" * size

    return send


def reading(document: TxtFile) -> Annotated[bytes,
                                            Download(filename="r.bin")]:
    """Reads a file and returns it as a download."""
    return Path(document).read_bytes()


def invoke(client, prefix=""):
    return client.post(f"{prefix}/send/invoke", json={"size": 4})


def names_in(directory):
    return sorted(entry.name for entry in directory.iterdir())


def stranger(directory, name, age=0, data=b"not ours"):
    """A file of the system temporary directory that nobody here wrote."""
    target = directory / name
    target.write_bytes(data)
    stale = now() - age

    os.utime(target, (stale, stale))

    return target


@pytest.fixture
def client(client_factory):
    return client_factory(naming("r.bin"))


@pytest.fixture
def process():
    """Several routers of one process, mounted side by side."""
    made = []

    def mount(*ttls):
        app = FastAPI()

        for index, ttl in enumerate(ttls):
            app.mount(f"/r{index}", app_of(naming("r.bin"), returns_ttl=ttl))

        client = TestClient(app)
        made.append(client)

        return client

    yield mount

    for client in made:
        client.close()


def test_a_returned_file_is_stored_under_its_date(client, returns_dir):
    before = now()
    result = invoke(client).json()["result"]
    stored = names_in(returns_dir)

    assert stored == [result["value"]]

    match = RETURNED_PATTERN.match(stored[0])

    assert match is not None
    assert match.group("name") == "r.bin"
    assert before <= int(match.group("stamp")) <= now()


def test_the_download_carries_the_public_name_and_never_the_physical_one(
    client,
):
    result = invoke(client).json()["result"]
    response = client.get(f"/returns/{result['value']}")
    disposition = response.headers["content-disposition"]

    assert response.status_code == 200
    assert response.content == b"xxxx"
    assert result["filename"] == "r.bin"
    assert disposition.endswith('filename="r.bin"')
    assert RETURNS_MARKER not in disposition
    assert PART_SUFFIX not in disposition


def test_an_expired_return_is_deleted_and_answers_404(client_factory,
                                                      returned_file,
                                                      returns_dir):
    expired = returned_file("r.bin", age=120, data=b"old")
    client = client_factory(naming("r.bin"), returns_ttl=60)

    assert not expired.exists()
    assert client.get(f"/returns/{expired.name}").status_code == 404
    assert names_in(returns_dir) == []


def test_a_fresh_return_survives_and_is_served_with_its_name(client_factory,
                                                             returned_file):
    fresh = returned_file("report.pdf", age=10, data=b"fresh")
    client = client_factory(naming("r.bin"), returns_ttl=60)
    response = client.get(f"/returns/{fresh.name}")

    assert response.status_code == 200
    assert response.content == b"fresh"
    assert response.headers["content-disposition"].endswith(
        'filename="report.pdf"'
    )


def test_a_return_exactly_at_the_ttl_has_expired(returned_file,
                                                 set_returns_ttl):
    expired = returned_file("r.bin", age=60)
    set_returns_ttl(60)

    returns_module.sweep()

    assert not expired.exists()


def test_a_return_just_under_the_ttl_stays(returned_file, set_returns_ttl):
    live = returned_file("r.bin", age=59)
    set_returns_ttl(60)

    returns_module.sweep()

    assert live.is_file()


def test_the_sweep_deletes_only_what_store_wrote(returns_dir, returned_file,
                                                 set_returns_ttl):
    set_returns_ttl(60)
    expired = returned_file("gone.bin", age=120)
    live = returned_file("live.bin", age=10)
    undated = stranger(returns_dir, f"{uuid4().hex}.legacy.pdf", age=120)
    theirs = [
        stranger(returns_dir, "tmpq3x9.tmp", age=120),
        stranger(returns_dir, "chunk.part", age=120),
        stranger(returns_dir, "notes.txt", age=120),
        stranger(returns_dir, f"{RETURNS_MARKER}0000000001~theirs.txt",
                 age=120),
        stranger(returns_dir, f"{uuid4().hex[:8]}.~r0000000001~short.pdf",
                 age=120),
        stranger(returns_dir, f"{uuid4().hex}.~r12~broken.pdf", age=120),
        stranger(returns_dir, f"{uuid4().hex}.~p0000000001~upload.pdf",
                 age=120),
    ]

    returns_module.sweep()

    assert not expired.exists()
    assert live.is_file()
    assert undated.read_bytes() == b"not ours"

    for path in theirs:
        assert path.read_bytes() == b"not ours"


def test_the_sweep_deletes_a_stale_partial_of_its_own(returns_dir,
                                                      set_returns_ttl):
    set_returns_ttl(60)
    dated = stamped_of("r.bin", now() - 120, RETURNS_MARKER)
    partial = returns_dir / f"{uuid4().hex}.{dated}.{uuid4().hex}{PART_SUFFIX}"
    partial.write_bytes(b"half")

    returns_module.sweep()

    assert not partial.exists()


def test_the_sweep_keeps_a_fresh_partial(returns_dir, set_returns_ttl):
    set_returns_ttl(60)
    dated = stamped_of("r.bin", now(), RETURNS_MARKER)
    partial = returns_dir / f"{uuid4().hex}.{dated}.{uuid4().hex}{PART_SUFFIX}"
    partial.write_bytes(b"half")

    returns_module.sweep()

    assert partial.read_bytes() == b"half"


def test_the_sweep_keeps_a_partial_of_somebody_else(returns_dir,
                                                    set_returns_ttl):
    set_returns_ttl(60)
    theirs = stranger(returns_dir, f"backup.{'z' * 32}{PART_SUFFIX}", age=120)

    returns_module.sweep()

    assert theirs.read_bytes() == b"not ours"


def test_the_sweep_survives_an_entry_it_cannot_delete(returns_dir,
                                                      returned_file,
                                                      set_returns_ttl):
    set_returns_ttl(60)
    dated = stamped_of("folder", now() - 120, RETURNS_MARKER)
    (returns_dir / f"{uuid4().hex}.{dated}").mkdir()
    expired = returned_file("gone.bin", age=120)

    returns_module.sweep()

    assert not expired.exists()
    assert len(names_in(returns_dir)) == 1


def test_the_router_sweeps_the_returns_directory_when_it_is_built(
    client_factory, returned_file
):
    expired = returned_file("gone.bin", age=120)

    client_factory(naming("r.bin"), returns_ttl=60)

    assert not expired.exists()


def test_a_return_stored_before_the_date_existed_still_downloads(
    client_factory, returns_dir
):
    legacy = stranger(returns_dir, f"{uuid4().hex}.report.pdf",
                      age=60 * 60 * 24, data=b"legacy")
    client = client_factory(naming("r.bin"), returns_ttl=60)
    response = client.get(f"/returns/{legacy.name}")

    assert response.status_code == 200
    assert response.content == b"legacy"
    assert response.headers["content-disposition"].endswith(
        'filename="report.pdf"'
    )


def test_without_a_ttl_the_return_carries_no_date(client_factory,
                                                  returns_dir):
    client = client_factory(naming("r.bin"), returns_ttl=None)
    reference = invoke(client).json()["result"]["value"]

    assert names_in(returns_dir) == [reference]
    assert RETURNED_PATTERN.match(reference) is None
    assert reference.endswith(".r.bin")
    assert client.get(f"/returns/{reference}").content == b"xxxx"


def test_without_a_ttl_nothing_is_ever_swept(client_factory, returned_file,
                                             returns_dir):
    ancient = returned_file("old.bin", age=60 * 60 * 24 * 365)

    client_factory(naming("r.bin"), returns_ttl=None)
    returns_module.sweep()

    assert names_in(returns_dir) == [ancient.name]


def test_the_sweeper_starts_for_the_returns_ttl_alone(client_factory,
                                                      sweeper_threads):
    client_factory(reading, pending_ttl=None, returns_ttl=60)

    assert len(sweeper_threads) == 1
    assert sweeper_threads[0].daemon is True
    assert sweeper_threads[0].target is upload_module._sweeping


def test_the_sweeper_starts_for_the_uploads_ttl_alone(client_factory,
                                                      sweeper_threads):
    client_factory(reading, pending_ttl=60, returns_ttl=None)

    assert len(sweeper_threads) == 1


def test_without_either_ttl_there_is_no_thread(client_factory,
                                               sweeper_threads):
    client_factory(reading, pending_ttl=None, returns_ttl=None)

    assert sweeper_threads == []


def test_the_sweeper_is_still_one_thread_for_both_directories(client_factory,
                                                              sweeper_threads):
    client_factory(reading, pending_ttl=60, returns_ttl=60)
    client_factory(reading, pending_ttl=60, returns_ttl=60)

    assert len(sweeper_threads) == 1


def test_each_pass_respects_its_own_ttl(client_factory, pending_file,
                                        returned_file):
    ancient_upload = pending_file("a.txt", age=60 * 60 * 24)
    expired_return = returned_file("r.bin", age=120)

    client_factory(reading, pending_ttl=None, returns_ttl=60)

    assert ancient_upload.is_file()
    assert not expired_return.exists()


def test_the_other_pair_expires_the_upload_and_keeps_the_return(
    client_factory, pending_file, returned_file
):
    expired_upload = pending_file("a.txt", age=120)
    ancient_return = returned_file("r.bin", age=60 * 60 * 24)

    client_factory(reading, pending_ttl=60, returns_ttl=None)

    assert not expired_upload.exists()
    assert ancient_return.is_file()


def test_two_routers_with_the_same_returns_ttl_settle_it_silently(
    process, sweeper_threads
):
    # filterwarnings=error, so a warning here would fail the test.
    process(60, 60)

    assert returns_module._ttl == 60
    assert len(sweeper_threads) == 1


def test_a_later_router_asking_for_another_returns_ttl_is_told_so(process):
    with pytest.warns(UserWarning, match=r"returns_ttl=7200 is ignored"):
        process(3600, 7200)

    assert returns_module._ttl == 3600


def test_a_later_router_asking_for_no_returns_ttl_is_told_so(process):
    with pytest.warns(UserWarning,
                      match=r"returns_ttl=None is ignored.*returns_ttl=3600"):
        process(3600, None)

    assert returns_module._ttl == 3600


def test_the_warning_names_the_router_that_asked(process):
    with pytest.warns(UserWarning) as records:
        process(3600, None)

    assert Path(records[0].filename).name == "test_returns_expiry.py"


def test_one_piece_of_prose_covers_both_ttls(client_factory):
    with pytest.warns(UserWarning) as records:
        client_factory(reading, pending_ttl=3600, returns_ttl=3600)
        client_factory(reading, pending_ttl=60, returns_ttl=60)

    said = [str(record.message) for record in records]

    assert len(said) == 2
    assert said[0].replace("pending_ttl", "ttl") == said[1].replace(
        "returns_ttl", "ttl"
    )


def test_the_process_returns_ttl_governs_every_app_of_the_process(
    process, returned_file
):
    with pytest.warns(UserWarning):
        process(60, None)

    expired = returned_file("gone.bin", age=120)

    with pytest.warns(UserWarning):
        process(None)

    assert not expired.exists()


def test_a_space_without_downloads_settles_nothing(client_factory, scalar,
                                                   sweeper_threads):
    client_factory(scalar, returns_ttl=None)
    client_factory(naming("r.bin"), returns_ttl=60)

    assert returns_module._ttl == 60
    assert len(sweeper_threads) == 1


@pytest.mark.parametrize("value", [0, -1, timedelta(0)])
def test_the_router_refuses_a_non_positive_returns_ttl(scalar, value):
    with pytest.raises(ValueError,
                       match="returns_ttl must be greater than zero"):
        app_of(scalar, returns_ttl=value)


@pytest.mark.parametrize("value", [True, 1.0, "60", b"60"])
def test_the_router_refuses_a_returns_ttl_of_another_type(scalar, value):
    with pytest.raises(TypeError,
                       match="returns_ttl must be int, timedelta or None"):
        app_of(scalar, returns_ttl=value)


def test_the_router_normalizes_a_returns_timedelta(client_factory):
    client_factory(naming("r.bin"), returns_ttl=timedelta(hours=2))

    assert returns_module._ttl == 7200


def test_checked_ttl_names_the_parameter_it_was_asked_about():
    with pytest.raises(TypeError,
                       match="returns_ttl must be int, timedelta or None"):
        checked_ttl("60", "returns_ttl")

    with pytest.raises(ValueError,
                       match="returns_ttl must be greater than zero"):
        checked_ttl(0, "returns_ttl")

    assert checked_ttl(timedelta(minutes=5), "returns_ttl") == 300
    assert checked_ttl(None, "returns_ttl") is None


@pytest.mark.parametrize("reference", ["~r", "~rreport.pdf",
                                       "~r0000000001~report.pdf"])
def test_a_reference_carrying_the_returns_marker_is_refused(client,
                                                            reference):
    assert client.get(f"/returns/{reference}").status_code == 404

    with pytest.raises(ValueError, match=RESERVED):
        stored_return(reference)


def test_a_file_on_disk_carrying_the_marker_is_never_served(client,
                                                            returns_dir):
    theirs = stranger(returns_dir, f"{RETURNS_MARKER}0000000001~theirs.txt")

    assert client.get(f"/returns/{theirs.name}").status_code == 404
    assert theirs.read_bytes() == b"not ours"


@pytest.mark.parametrize("marker", [PENDING_MARKER, RETURNS_MARKER])
def test_the_shared_check_refuses_every_reserved_marker(marker):
    with pytest.raises(ValueError,
                       match=f"reserved prefix '{marker}'"):
        segment_of(f"{marker}report.pdf")


def test_an_upload_reference_carrying_the_returns_marker_is_refused(
    client_factory, uploads_dir
):
    client = client_factory(reading)
    response = client.post("/upload", content=b"x",
                           headers={"X-File-Reference": "~r0000000001~a.txt"})

    assert response.status_code == 400
    assert response.json() == {"detail": f"X-File-Reference {RESERVED}"}
    assert names_in(uploads_dir) == []


def test_the_longest_filename_the_contract_takes_still_fits_the_disk(
    client_factory, returns_dir
):
    filename = "n" * (FILENAME_LIMIT - 4) + ".bin"
    client = client_factory(naming(filename), returns_ttl=3600)
    result = invoke(client).json()["result"]
    reference = result["value"]

    assert len(filename.encode("utf-8")) == FILENAME_LIMIT
    assert len(reference.encode("utf-8")) == RETURN_LIMIT
    assert len(reference.encode("utf-8")) + PARTIAL_SUFFIX <= NAME_LIMIT
    assert result["filename"] == filename
    assert client.get(f"/returns/{reference}").content == b"xxxx"


def test_one_byte_over_that_limit_never_reaches_the_disk(client_factory,
                                                         returns_dir):
    filename = "n" * (FILENAME_LIMIT + 1)
    client = client_factory(naming(filename))
    response = invoke(client)

    assert response.status_code == 500
    assert response.json() == {
        "error": f"ReturnContractError: Download filename: is longer than "
                 f"{FILENAME_LIMIT} bytes, got {filename!r}"
    }
    assert names_in(returns_dir) == []


def test_a_filename_one_byte_over_the_limit_fails_the_shared_check():
    with pytest.raises(ValueError,
                       match=f"is longer than {FILENAME_LIMIT} bytes"):
        segment_of("n" * (FILENAME_LIMIT + 1), FILENAME_LIMIT)


def test_the_filename_limit_leaves_room_for_what_store_prepends():
    dated = stamped_of("n" * FILENAME_LIMIT, 9999999999, RETURNS_MARKER)
    longest = f"{TOKEN}.{dated}"

    assert FILENAME_LIMIT == RETURN_LIMIT - IDENTIFIER_PREFIX - RETURNS_PREFIX
    assert RETURN_LIMIT == NAME_LIMIT - PARTIAL_SUFFIX
    assert len(longest) == RETURN_LIMIT
    assert len(f"{longest}.{TOKEN}{PART_SUFFIX}") == NAME_LIMIT


def test_a_returned_name_parses_back_to_its_public_name():
    stamp, filename = returned_of(f"{TOKEN}.~r1234567890~report.pdf")

    assert (stamp, filename) == (1234567890, "report.pdf")
    assert stamped_of(filename, stamp, RETURNS_MARKER) == (
        "~r1234567890~report.pdf"
    )


@pytest.mark.parametrize("name", [
    "report.pdf",
    f"{TOKEN}.report.pdf",
    f"{TOKEN}~r1234567890~report.pdf",
    f"{TOKEN}.~r123456789~report.pdf",
    f"{TOKEN}.~r12345678901~report.pdf",
    f"{TOKEN}.~r1234567890-report.pdf",
    f"{TOKEN}.~r1234567890~",
    f"{TOKEN}.~p1234567890~report.pdf",
    f"{'z' * 32}.~r1234567890~report.pdf",
    f"{'0' * 31}.~r1234567890~report.pdf",
    f"{'0' * 33}.~r1234567890~report.pdf",
    "~r1234567890~report.pdf",
])
def test_what_is_not_a_returned_name_does_not_parse(name):
    assert returned_of(name) is None
