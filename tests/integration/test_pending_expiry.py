import json
import os
import re
from datetime import timedelta
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import func_to_web.web.upload as upload_module
from func_to_web import IsPathFile, app_of
from func_to_web.web.pending import PART_SUFFIX, now, parsed, pending_of
from func_to_web.web.references import (
    NAME_LIMIT,
    PENDING_PREFIX,
    REFERENCE_LIMIT,
)
from func_to_web.web.upload import CONFLICT, DEFAULT_TTL, checked_ttl

PENDING_PATTERN = re.compile(r"^~p(?P<stamp>\d{10})~(?P<reference>.+)$")

BRACKETS = "report[1].txt"

TxtFile = Annotated[str, IsPathFile(extensions=(".txt",))]


def send(client, reference, content=b"body", prefix=""):
    return client.post(f"{prefix}/upload", content=content,
                       headers={"X-File-Reference": reference})


def invoke(client, reference):
    return client.post("/read/invoke", json={"document": reference})


def prefill(client, reference):
    return client.get("/read/",
                      params={"prefill": json.dumps({"document": reference})})


def names_in(directory):
    return sorted(entry.name for entry in directory.iterdir())


@pytest.fixture
def client(client_factory, file_function):
    return client_factory(file_function)


@pytest.fixture
def process(file_function):
    """Several routers of one process, mounted side by side.

    The TTL is the only piece of this design that lives in module state, so
    it is the only one a refactor can break without a unit test noticing.
    """
    made = []

    def mount(*ttls):
        app = FastAPI()

        for index, ttl in enumerate(ttls):
            app.mount(f"/r{index}", app_of(file_function, pending_ttl=ttl))

        client = TestClient(app)
        made.append(client)

        return client

    yield mount

    for client in made:
        client.close()


class Vanishing:
    """os.replace as another execution promoting the file first."""

    def __init__(self, target, data):
        self.target = target
        self.data = data
        self.attempts = 0

    def replace(self, source, destination):
        self.attempts += 1

        if self.attempts == 1:
            Path(source).unlink()
            self.target.write_bytes(self.data)

            raise FileNotFoundError(2, "No such file or directory")

        raise AssertionError("the second attempt should read the bare name")


def test_an_upload_is_published_as_pending(client, uploads_dir):
    before = now()
    response = send(client, "a.txt", b"body")
    stored = names_in(uploads_dir)

    assert response.status_code == 200
    assert len(stored) == 1

    match = PENDING_PATTERN.match(stored[0])

    assert match is not None
    assert match.group("reference") == "a.txt"
    assert before <= int(match.group("stamp")) <= now()
    assert (uploads_dir / stored[0]).read_bytes() == b"body"


def test_the_client_only_ever_names_the_bare_reference(client, uploads_dir):
    assert send(client, "a.txt", b"hello").json() == {"uploaded": True}

    answer = invoke(client, "a.txt")

    assert answer.status_code == 200
    assert answer.json()["result"]["value"] == "hello"
    assert names_in(uploads_dir) == ["a.txt"]


def test_an_invocation_promotes_the_pending_file(client, uploads_dir):
    send(client, "a.txt", b"hello")

    answer = invoke(client, "a.txt")

    assert answer.status_code == 200
    assert (uploads_dir / "a.txt").read_bytes() == b"hello"
    assert names_in(uploads_dir) == ["a.txt"]


def test_the_function_receives_the_bare_path(client_factory, uploads_dir):
    seen = []

    def keep(document: TxtFile) -> str:
        seen.append(document)
        return "ok"

    client = client_factory(keep)

    assert send(client, "a.txt", b"hello").status_code == 200
    assert client.post("/keep/invoke",
                       json={"document": "a.txt"}).status_code == 200
    assert seen == [str((uploads_dir / "a.txt").resolve())]


def test_a_prefill_promotes_the_pending_file(client, uploads_dir):
    send(client, "a.txt", b"hello")

    answer = prefill(client, "a.txt")

    assert answer.status_code == 200
    assert (uploads_dir / "a.txt").read_bytes() == b"hello"
    assert names_in(uploads_dir) == ["a.txt"]


def test_a_second_resolution_uses_the_promoted_file(client, uploads_dir,
                                                    monkeypatch):
    send(client, "a.txt", b"hello")

    assert invoke(client, "a.txt").status_code == 200

    class Refusing:
        def replace(self, source, destination):
            raise AssertionError("a promoted file is never renamed again")

    monkeypatch.setattr(upload_module, "os", Refusing())

    assert invoke(client, "a.txt").status_code == 200
    assert prefill(client, "a.txt").status_code == 200
    assert names_in(uploads_dir) == ["a.txt"]


def test_the_oldest_pending_file_wins(client_factory, file_function,
                                      uploads_dir, pending_file):
    pending_file("a.txt", age=30, data=b"first")
    pending_file("a.txt", age=10, data=b"second")
    client = client_factory(file_function)

    answer = invoke(client, "a.txt")

    assert answer.status_code == 200
    assert answer.json()["result"]["value"] == "first"
    assert (uploads_dir / "a.txt").read_bytes() == b"first"


def test_an_expired_pending_file_does_not_hide_a_live_one(client_factory,
                                                           file_function,
                                                           uploads_dir,
                                                           pending_file):
    # Planted after the router, so it is the resolver that meets them and not
    # the sweep the router runs when it is built.
    client = client_factory(file_function, pending_ttl=60)
    expired = pending_file("a.txt", age=120, data=b"first")
    pending_file("a.txt", age=10, data=b"second")

    answer = invoke(client, "a.txt")

    assert answer.status_code == 200
    assert answer.json()["result"]["value"] == "second"
    assert not expired.exists()
    assert names_in(uploads_dir) == ["a.txt"]


def test_every_expired_pending_file_is_discarded_on_the_way(client_factory,
                                                             file_function,
                                                             uploads_dir,
                                                             pending_file):
    client = client_factory(file_function, pending_ttl=60)
    older = pending_file("a.txt", age=300, data=b"first")
    expired = pending_file("a.txt", age=120, data=b"second")
    pending_file("a.txt", age=10, data=b"third")

    answer = invoke(client, "a.txt")

    assert answer.json()["result"]["value"] == "third"
    assert not older.exists()
    assert not expired.exists()
    assert names_in(uploads_dir) == ["a.txt"]


def test_an_expired_pending_file_is_not_found_by_invoke(client_factory,
                                                        file_function,
                                                        uploads_dir,
                                                        pending_file):
    pending_file("a.txt", age=120)
    client = client_factory(file_function, pending_ttl=60)

    answer = invoke(client, "a.txt")

    assert answer.status_code == 422
    assert answer.json() == {
        "error": "FileNotFoundError: File not found: a.txt"
    }
    assert names_in(uploads_dir) == []


def test_an_expired_pending_file_is_not_found_by_prefill(client_factory,
                                                         file_function,
                                                         uploads_dir,
                                                         pending_file):
    pending_file("a.txt", age=120)
    client = client_factory(file_function, pending_ttl=60)

    answer = prefill(client, "a.txt")

    assert answer.status_code == 400
    assert answer.json() == {"detail": "File not found: a.txt"}
    assert names_in(uploads_dir) == []


def test_a_pending_file_exactly_at_the_ttl_has_expired(client_factory,
                                                       file_function,
                                                       pending_file):
    pending_file("a.txt", age=60)
    client = client_factory(file_function, pending_ttl=60)

    assert invoke(client, "a.txt").status_code == 422


def test_a_pending_file_just_under_the_ttl_still_resolves(client_factory,
                                                          file_function,
                                                          pending_file):
    pending_file("a.txt", age=59, data=b"hello")
    client = client_factory(file_function, pending_ttl=60)

    assert invoke(client, "a.txt").json()["result"]["value"] == "hello"


def test_a_promoted_reference_is_refused_a_second_upload(client):
    send(client, "a.txt", b"one")

    assert invoke(client, "a.txt").status_code == 200

    response = send(client, "a.txt", b"two")

    assert response.status_code == CONFLICT
    assert response.json() == {
        "detail": "a file with this reference already exists"
    }


@pytest.mark.parametrize("age", [0, 30, 60 * 60 * 24 * 365])
def test_a_pending_reference_is_refused_a_second_upload(client, pending_file,
                                                        age):
    pending_file("a.txt", age=age)

    assert send(client, "a.txt", b"two").status_code == CONFLICT


@pytest.mark.parametrize("reference", ["~p", "~pa.txt", "~p0000000001~a.txt"])
def test_a_reference_carrying_the_reserved_prefix_is_refused(client,
                                                             uploads_dir,
                                                             reference):
    response = send(client, reference)

    assert response.status_code == 400
    assert response.json() == {
        "detail": "X-File-Reference cannot start with the reserved prefix '~p'"
    }
    assert names_in(uploads_dir) == []


def test_the_reserved_prefix_cannot_be_invoked_either(client, pending_file):
    target = pending_file("a.txt")

    answer = invoke(client, target.name)

    assert answer.status_code == 422
    assert answer.json()["error"] == (
        f"ValueError: invalid file reference {target.name!r}: "
        "cannot start with the reserved prefix '~p'"
    )
    assert target.is_file()


def test_a_reference_with_brackets_lives_the_whole_cycle(client, uploads_dir):
    assert send(client, BRACKETS, b"hello").status_code == 200

    stored = names_in(uploads_dir)

    assert PENDING_PATTERN.match(stored[0]).group("reference") == BRACKETS
    assert send(client, BRACKETS, b"other").status_code == CONFLICT

    answer = invoke(client, BRACKETS)

    assert answer.status_code == 200
    assert answer.json()["result"]["value"] == "hello"
    assert names_in(uploads_dir) == [BRACKETS]


def test_a_pending_file_with_brackets_expires_like_any_other(client_factory,
                                                             file_function,
                                                             uploads_dir,
                                                             pending_file):
    pending_file(BRACKETS, age=120)
    client = client_factory(file_function, pending_ttl=60)

    assert invoke(client, BRACKETS).status_code == 422
    assert names_in(uploads_dir) == []


def test_the_sweep_deletes_what_is_expired_and_keeps_what_is_not(uploads_dir,
                                                                 pending_file,
                                                                 set_ttl):
    set_ttl(60)
    promoted = uploads_dir / "kept.txt"
    promoted.write_bytes(b"kept")
    live = pending_file("live.txt", age=10)
    expired = pending_file("gone.txt", age=120)
    malformed = uploads_dir / "~p12~broken.txt"
    malformed.write_bytes(b"x")
    undated = uploads_dir / "~p0000000001~"
    undated.write_bytes(b"x")
    old_part = uploads_dir / f"stale.txt.{'0' * 32}{PART_SUFFIX}"
    old_part.write_bytes(b"x")
    fresh_part = uploads_dir / f"fresh.txt.{'1' * 32}{PART_SUFFIX}"
    fresh_part.write_bytes(b"x")
    stale = now() - 120

    os.utime(old_part, (stale, stale))

    upload_module.sweep()

    assert promoted.is_file()
    assert live.is_file()
    assert fresh_part.is_file()
    assert not expired.exists()
    assert not malformed.exists()
    assert not undated.exists()
    assert not old_part.exists()


def test_the_sweep_keeps_a_promoted_reference_that_ends_in_part(uploads_dir,
                                                                set_ttl):
    set_ttl(60)
    promoted = uploads_dir / f"notes-{'a' * 8}{PART_SUFFIX}"
    promoted.write_bytes(b"kept")
    stale = now() - 120

    os.utime(promoted, (stale, stale))
    upload_module.sweep()

    assert promoted.read_bytes() == b"kept"


def test_the_sweep_keeps_a_promoted_reference_with_a_short_token(uploads_dir,
                                                                 set_ttl):
    set_ttl(60)
    promoted = uploads_dir / f"notes.{'a' * 31}{PART_SUFFIX}"
    promoted.write_bytes(b"kept")
    stale = now() - 120

    os.utime(promoted, (stale, stale))
    upload_module.sweep()

    assert promoted.read_bytes() == b"kept"


def test_the_sweep_keeps_a_promoted_reference_with_a_non_hex_token(uploads_dir,
                                                                   set_ttl):
    set_ttl(60)
    promoted = uploads_dir / f"notes.{'z' * 32}{PART_SUFFIX}"
    promoted.write_bytes(b"kept")
    stale = now() - 120

    os.utime(promoted, (stale, stale))
    upload_module.sweep()

    assert promoted.read_bytes() == b"kept"


def test_the_sweep_still_deletes_a_real_stale_partial(uploads_dir, set_ttl):
    set_ttl(60)
    partial = uploads_dir / f"notes.txt.{uuid4().hex}{PART_SUFFIX}"
    partial.write_bytes(b"half")
    stale = now() - 120

    os.utime(partial, (stale, stale))
    upload_module.sweep()

    assert not partial.exists()


def test_the_sweep_keeps_a_fresh_partial(uploads_dir, set_ttl):
    set_ttl(60)
    partial = uploads_dir / f"notes.txt.{uuid4().hex}{PART_SUFFIX}"
    partial.write_bytes(b"half")

    upload_module.sweep()

    assert partial.read_bytes() == b"half"


def test_a_promoted_reference_ending_in_part_stays_immutable(client_factory,
                                                             uploads_dir,
                                                             file_function,
                                                             set_ttl):
    reference = f"notes-{'a' * 8}{PART_SUFFIX}"
    client = client_factory(file_function, pending_ttl=60)
    set_ttl(60)

    first = client.post("/upload", content=b"first",
                        headers={"X-File-Reference": reference})

    assert first.status_code == 200

    promoted = uploads_dir / reference
    stale = now() - 120

    upload_module.stored_file(reference)
    os.utime(promoted, (stale, stale))
    upload_module.sweep()

    second = client.post("/upload", content=b"second",
                         headers={"X-File-Reference": reference})

    assert promoted.read_bytes() == b"first"
    assert second.status_code == 409


def test_the_sweep_survives_a_directory_it_cannot_delete(uploads_dir,
                                                         pending_file, set_ttl):
    set_ttl(60)
    (uploads_dir / "folder").mkdir()
    expired = pending_file("gone.txt", age=120)

    upload_module.sweep()

    assert (uploads_dir / "folder").is_dir()
    assert not expired.exists()


def test_the_router_sweeps_when_it_is_built(client_factory, file_function,
                                            uploads_dir, pending_file):
    expired = pending_file("gone.txt", age=120)

    client_factory(file_function, pending_ttl=60)

    assert not expired.exists()


def test_the_sweeper_is_one_daemon_thread_per_process(client_factory,
                                                      file_function,
                                                      sweeper_threads):
    client_factory(file_function)
    client_factory(file_function)

    assert len(sweeper_threads) == 1
    assert sweeper_threads[0].daemon is True
    assert sweeper_threads[0].target is upload_module._sweeping


def test_two_routers_with_the_same_ttl_settle_it_silently(process,
                                                          sweeper_threads):
    # filterwarnings=error, so a warning here would fail the test.
    process(60, 60)

    assert upload_module._ttl == 60
    assert len(sweeper_threads) == 1


def test_a_later_router_asking_for_another_ttl_is_told_it_was_ignored(process):
    with pytest.warns(UserWarning, match=r"pending_ttl=7200 is ignored"):
        process(3600, 7200)

    assert upload_module._ttl == 3600


def test_a_later_router_asking_for_no_ttl_is_told_it_was_ignored(process):
    with pytest.warns(UserWarning,
                      match=r"pending_ttl=None is ignored.*pending_ttl=3600"):
        process(3600, None)

    assert upload_module._ttl == 3600


def test_the_warning_names_the_router_that_asked(process):
    with pytest.warns(UserWarning) as records:
        process(3600, None)

    assert Path(records[0].filename).name == "test_pending_expiry.py"


def test_a_router_that_lost_its_ttl_still_publishes_pending(process,
                                                            uploads_dir):
    with pytest.warns(UserWarning):
        client = process(3600, None)

    assert send(client, "a.txt", b"hello", prefix="/r1").status_code == 200
    assert PENDING_PATTERN.match(names_in(uploads_dir)[0]) is not None


def test_the_process_ttl_governs_every_app_of_the_process(process,
                                                             pending_file,
                                                             uploads_dir):
    pending_file("a.txt", age=120)

    with pytest.warns(UserWarning):
        client = process(60, None)

    # Same directory, same policy: the second router resolves and expires
    # under the TTL the first one settled, not under its own.
    answer = client.post("/r1/read/invoke", json={"document": "a.txt"})

    assert answer.status_code == 422
    assert names_in(uploads_dir) == []


def test_a_later_router_sweeps_with_the_adopted_ttl(process, pending_file):
    with pytest.warns(UserWarning):
        process(60, None)

    expired = pending_file("gone.txt", age=120)

    with pytest.warns(UserWarning):
        process(None)

    assert not expired.exists()


def test_a_router_without_file_fields_settles_nothing(client_factory, scalar,
                                                      file_function,
                                                      sweeper_threads):
    client_factory(scalar, pending_ttl=None)
    client_factory(file_function, pending_ttl=60)

    assert upload_module._ttl == 60
    assert len(sweeper_threads) == 1


def test_the_sweeper_sleeps_a_new_stretch_every_cycle(monkeypatch, uploads_dir,
                                                      set_ttl):
    set_ttl(60)
    drawn = []
    slept = []

    def draw(low, high):
        drawn.append((low, high))
        return 1234.0

    def stop(seconds):
        slept.append(seconds)

        if len(slept) == 3:
            raise KeyboardInterrupt

    monkeypatch.setattr(upload_module, "uniform", draw)
    monkeypatch.setattr(upload_module, "sleep", stop)

    with pytest.raises(KeyboardInterrupt):
        upload_module._sweeping()

    assert drawn == [(upload_module.SWEEP_MIN_SECONDS,
                      upload_module.SWEEP_MAX_SECONDS)] * 3
    assert slept == [1234.0] * 3


def test_without_a_ttl_the_upload_is_published_bare(client_factory,
                                                    file_function, uploads_dir,
                                                    sweeper_threads):
    client = client_factory(file_function, pending_ttl=None)

    assert send(client, "a.txt", b"hello").status_code == 200
    assert names_in(uploads_dir) == ["a.txt"]
    assert (uploads_dir / "a.txt").read_bytes() == b"hello"
    assert invoke(client, "a.txt").json()["result"]["value"] == "hello"
    assert sweeper_threads == []


def test_without_a_ttl_nothing_is_ever_swept(client_factory, file_function,
                                             uploads_dir, pending_file):
    ancient = pending_file("old.txt", age=60 * 60 * 24 * 365)

    client_factory(file_function, pending_ttl=None)
    upload_module.sweep()

    assert ancient.is_file()
    assert names_in(uploads_dir) == [ancient.name]


def test_without_a_ttl_a_pending_file_is_still_promoted(client_factory,
                                                        file_function,
                                                        uploads_dir,
                                                        pending_file):
    pending_file("a.txt", age=60 * 60 * 24 * 365, data=b"hello")
    client = client_factory(file_function, pending_ttl=None)

    assert invoke(client, "a.txt").json()["result"]["value"] == "hello"
    assert names_in(uploads_dir) == ["a.txt"]


def test_checked_ttl_accepts_none():
    assert checked_ttl(None, "pending_ttl") is None


@pytest.mark.parametrize("value", [1, 60, DEFAULT_TTL, 60 * 60 * 24])
def test_checked_ttl_accepts_a_positive_int(value):
    assert checked_ttl(value, "pending_ttl") == value


@pytest.mark.parametrize(("value", "seconds"), [
    (timedelta(seconds=1), 1),
    (timedelta(minutes=5), 300),
    (timedelta(days=1), 86400),
    (timedelta(seconds=1.5), 1),
])
def test_checked_ttl_normalizes_a_timedelta(value, seconds):
    assert checked_ttl(value, "pending_ttl") == seconds


@pytest.mark.parametrize("value", [True, False, 1.0, "60", b"60", object()])
def test_checked_ttl_rejects_another_type(value):
    with pytest.raises(TypeError,
                       match="pending_ttl must be int, timedelta or None"):
        checked_ttl(value, "pending_ttl")


@pytest.mark.parametrize("value", [
    0,
    -1,
    timedelta(0),
    timedelta(seconds=-1),
    timedelta(microseconds=1),
])
def test_checked_ttl_rejects_what_is_not_a_whole_positive_second(value):
    with pytest.raises(ValueError,
                       match="pending_ttl must be greater than zero"):
        checked_ttl(value, "pending_ttl")


@pytest.mark.parametrize("value", [0, -1, timedelta(0)])
def test_the_router_refuses_a_non_positive_ttl(scalar, value):
    with pytest.raises(ValueError, match="greater than zero"):
        app_of(scalar, pending_ttl=value)


@pytest.mark.parametrize("value", [True, 1.0, "60"])
def test_the_router_refuses_a_ttl_of_another_type(scalar, value):
    with pytest.raises(TypeError, match="pending_ttl must be int"):
        app_of(scalar, pending_ttl=value)


def test_the_router_accepts_a_timedelta(file_function):
    assert app_of(file_function, pending_ttl=timedelta(hours=2)) is not None


def test_a_promotion_race_falls_back_to_the_bare_name(client_factory,
                                                      file_function,
                                                      uploads_dir,
                                                      pending_file,
                                                      monkeypatch):
    pending_file("a.txt", data=b"hello")
    client = client_factory(file_function)
    vanishing = Vanishing(uploads_dir / "a.txt", b"hello")
    monkeypatch.setattr(upload_module, "os", vanishing)

    answer = invoke(client, "a.txt")

    assert answer.status_code == 200
    assert answer.json()["result"]["value"] == "hello"
    assert vanishing.attempts == 1
    assert names_in(uploads_dir) == ["a.txt"]


def test_a_reference_at_the_new_limit_still_fits_its_pending_name(client,
                                                                  uploads_dir):
    reference = "a" * (REFERENCE_LIMIT - 4) + ".txt"

    assert send(client, reference, b"body").status_code == 200

    stored = names_in(uploads_dir)[0]

    assert len(stored.encode("utf-8")) <= NAME_LIMIT
    assert PENDING_PATTERN.match(stored).group("reference") == reference
    assert invoke(client, reference).status_code == 200


def test_one_byte_over_the_new_limit_is_refused(client, uploads_dir):
    response = send(client, "a" * (REFERENCE_LIMIT + 1))

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"X-File-Reference is longer than {REFERENCE_LIMIT} bytes"
    }
    assert names_in(uploads_dir) == []


def test_the_limit_leaves_room_for_the_prefix_and_the_partial_suffix():
    assert REFERENCE_LIMIT == 255 - len(".{}.part".format("0" * 32)) - 13
    assert PENDING_PREFIX == 13
    assert len(pending_of("a" * REFERENCE_LIMIT, now())) <= NAME_LIMIT


def test_files_stored_before_this_version_survive_the_sweep(uploads_dir,
                                                            set_ttl):
    set_ttl(1)
    names = ["report.pdf", "a.txt", BRACKETS, "no-extension"]

    for name in names:
        (uploads_dir / name).write_bytes(name.encode("utf-8"))

    upload_module.sweep()

    assert names_in(uploads_dir) == sorted(names)


def test_a_reference_longer_than_the_new_limit_still_resolves(client_factory,
                                                              file_function,
                                                              uploads_dir):
    # 2.0 minted up to 217 bytes. The new limit guards writing, never
    # reading, so what is already on disk stays reachable.
    legacy = "a" * (REFERENCE_LIMIT + 6) + ".txt"
    (uploads_dir / legacy).write_bytes(b"legacy")
    client = client_factory(file_function)

    answer = invoke(client, legacy)

    assert len(legacy.encode("utf-8")) > REFERENCE_LIMIT
    assert answer.status_code == 200
    assert answer.json()["result"]["value"] == "legacy"


def test_that_reference_can_no_longer_be_uploaded_again(client_factory,
                                                        file_function,
                                                        uploads_dir):
    legacy = "a" * (REFERENCE_LIMIT + 6) + ".txt"
    (uploads_dir / legacy).write_bytes(b"legacy")
    client = client_factory(file_function)

    # Not a regression: it is already stored, so a second upload was a 409
    # before and is a 400 now. Either way the bytes are untouched.
    response = send(client, legacy, b"other")

    assert response.status_code == 400
    assert (uploads_dir / legacy).read_bytes() == b"legacy"


def test_files_stored_before_this_version_still_resolve(client_factory,
                                                        file_function,
                                                        uploads_dir):
    (uploads_dir / "a.txt").write_bytes(b"legacy")
    client = client_factory(file_function, pending_ttl=1)

    answer = invoke(client, "a.txt")

    assert answer.status_code == 200
    assert answer.json()["result"]["value"] == "legacy"
    assert names_in(uploads_dir) == ["a.txt"]


@pytest.mark.parametrize("name", [
    "~p1234567890~a.txt",
    "~p0000000000~a.txt",
    "~p9999999999~a.txt",
])
def test_a_pending_name_parses_back_to_its_reference(name):
    stamp, reference = parsed(name)

    assert reference == "a.txt"
    assert pending_of(reference, stamp) == name


@pytest.mark.parametrize("name", [
    "a.txt",
    "~pa.txt",
    "~p123456789~a.txt",
    "~p12345678901~a.txt",
    "~p1234567890-a.txt",
    "~p1234567890~",
    "~p-123456789~a.txt",
    "~p١٢٣٤٥٦٧٨٩٠~a.txt",
    "~p1234567890",
])
def test_what_is_not_a_pending_name_does_not_parse(name):
    assert parsed(name) is None
