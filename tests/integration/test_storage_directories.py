import json
from pathlib import Path

import pytest

from shared import carries
from func_to_web import app_of
from func_to_web.config import RETURNS_VARIABLE, UPLOADS_VARIABLE
from func_to_web.web import returned_files
from func_to_web.web import upload as upload_module
from func_to_web.web.messages import without_storage_paths
from func_to_web.web.pending import now, pending_of, stamped_of
from func_to_web.web.references import RETURNS_MARKER

WRONG_TYPES = [3, 3.5, True, b"/srv/uploads", ["/srv/uploads"], object()]


def names_in(directory):
    return sorted(entry.name for entry in directory.iterdir())


def send(client, reference, content=b"body"):
    return client.post("/upload", content=content,
                       headers={"X-File-Reference": reference})


def skeleton(message, name, asked, settled):
    """The warning with its name and its two values taken out."""
    return (message.replace(f"{name}={asked!r}", "<asked>")
                   .replace(f"{name}={settled!r}", "<settled>"))


@pytest.fixture
def uploading(client_factory, file_function):
    def make(**options):
        return client_factory(file_function, **options)

    return make


@pytest.fixture
def returning(client_factory, downloading):
    def make(**options):
        return client_factory(downloading, **options)

    return make


def test_the_uploads_argument_beats_the_variable_and_the_default(
    uploading, tmp_path, monkeypatch
):
    monkeypatch.setenv(UPLOADS_VARIABLE, str(tmp_path / "variable"))
    monkeypatch.setattr("func_to_web.config.UPLOADS_DIR", tmp_path / "default")

    uploading(uploads_dir=tmp_path / "argument")

    assert upload_module.UPLOADS_DIR == tmp_path / "argument"


def test_the_uploads_variable_beats_the_default(uploading, tmp_path,
                                                monkeypatch):
    monkeypatch.setenv(UPLOADS_VARIABLE, str(tmp_path / "variable"))
    monkeypatch.setattr("func_to_web.config.UPLOADS_DIR", tmp_path / "default")

    uploading()

    assert upload_module.UPLOADS_DIR == tmp_path / "variable"


def test_the_uploads_default_is_used_when_nothing_asks(uploading, tmp_path,
                                                       monkeypatch):
    monkeypatch.delenv(UPLOADS_VARIABLE)
    monkeypatch.setattr("func_to_web.config.UPLOADS_DIR", tmp_path / "default")

    uploading()

    assert upload_module.UPLOADS_DIR == tmp_path / "default"


def test_the_returns_argument_beats_the_variable_and_the_default(
    returning, tmp_path, monkeypatch
):
    monkeypatch.setenv(RETURNS_VARIABLE, str(tmp_path / "variable"))
    monkeypatch.setattr("func_to_web.config.RETURNS_DIR", tmp_path / "default")

    returning(returns_dir=tmp_path / "argument")

    assert returned_files.RETURNS_DIR == tmp_path / "argument"


def test_the_returns_variable_beats_the_default(returning, tmp_path,
                                                monkeypatch):
    monkeypatch.setenv(RETURNS_VARIABLE, str(tmp_path / "variable"))
    monkeypatch.setattr("func_to_web.config.RETURNS_DIR", tmp_path / "default")

    returning()

    assert returned_files.RETURNS_DIR == tmp_path / "variable"


def test_the_returns_default_is_used_when_nothing_asks(returning, tmp_path,
                                                       monkeypatch):
    monkeypatch.delenv(RETURNS_VARIABLE)
    monkeypatch.setattr("func_to_web.config.RETURNS_DIR", tmp_path / "default")

    returning()

    assert returned_files.RETURNS_DIR == tmp_path / "default"


@pytest.mark.parametrize("value", WRONG_TYPES)
def test_an_uploads_dir_of_another_type_is_refused(file_function, value):
    with pytest.raises(TypeError,
                       match="uploads_dir must be str, Path or None"):
        app_of(file_function, uploads_dir=value)


@pytest.mark.parametrize("value", WRONG_TYPES)
def test_a_returns_dir_of_another_type_is_refused(file_function, value):
    with pytest.raises(TypeError,
                       match="returns_dir must be str, Path or None"):
        app_of(file_function, returns_dir=value)


def test_a_type_is_refused_even_for_a_space_that_stores_nothing(scalar):
    with pytest.raises(TypeError, match="uploads_dir must be"):
        app_of(scalar, uploads_dir=3)


def test_a_path_that_is_not_a_directory_is_refused(file_function, tmp_path):
    occupied = tmp_path / "taken.txt"
    occupied.write_bytes(b"x")

    with pytest.raises(ValueError, match="uploads_dir is not a directory"):
        app_of(file_function, uploads_dir=occupied)

    with pytest.raises(ValueError, match="returns_dir is not a directory"):
        app_of(file_function, returns_dir=occupied)


def test_a_missing_directory_is_created_when_the_router_is_built(
    file_function, tmp_path
):
    target = tmp_path / "deep" / "nested" / "uploads"

    app_of(file_function, uploads_dir=target)

    assert target.is_dir()


def test_both_directories_are_created_by_a_space_that_stores_nothing(scalar,
                                                                     tmp_path):
    app_of(scalar, uploads_dir=tmp_path / "u", returns_dir=tmp_path / "r")

    assert (tmp_path / "u").is_dir()
    assert (tmp_path / "r").is_dir()


def test_an_existing_directory_is_taken_as_it_is(uploading, tmp_path):
    ready = tmp_path / "ready"
    ready.mkdir()
    (ready / "planted.txt").write_bytes(b"planted")

    client = uploading(uploads_dir=ready)

    assert send(client, "planted.txt").status_code == 409
    assert (ready / "planted.txt").read_bytes() == b"planted"


def test_a_directory_that_cannot_be_created_fails_the_build(file_function,
                                                             tmp_path,
                                                             monkeypatch):
    def refuse(self, mode=0o777, parents=False, exist_ok=False):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(Path, "mkdir", refuse)

    with pytest.raises(PermissionError):
        app_of(file_function, uploads_dir=tmp_path / "denied")


def test_a_string_is_accepted(uploading, tmp_path):
    uploading(uploads_dir=str(tmp_path / "as-a-string"))

    assert upload_module.UPLOADS_DIR == tmp_path / "as-a-string"


def test_a_relative_directory_is_made_absolute(uploading, tmp_path,
                                               monkeypatch):
    monkeypatch.chdir(tmp_path)

    uploading(uploads_dir="relative-uploads")

    assert upload_module.UPLOADS_DIR.is_absolute()
    assert upload_module.UPLOADS_DIR == (Path.cwd() / "relative-uploads"
                                         ).resolve()


def test_the_variable_alone_moves_the_uploads(uploading, uploads_dir, tmp_path,
                                              monkeypatch):
    custom = tmp_path / "by-variable"
    monkeypatch.setenv(UPLOADS_VARIABLE, str(custom))

    client = uploading()

    assert send(client, "a.txt", b"hello").status_code == 200
    assert names_in(uploads_dir) == []
    assert len(names_in(custom)) == 1


def test_the_variable_alone_moves_the_returns(returning, returns_dir, tmp_path,
                                              monkeypatch):
    custom = tmp_path / "by-variable"
    monkeypatch.setenv(RETURNS_VARIABLE, str(custom))

    client = returning()
    result = client.post("/bundle/invoke", json={}).json()["result"]

    assert names_in(returns_dir) == []
    assert names_in(custom) == [result["value"]]


def test_a_later_router_asking_for_another_uploads_dir_is_told_it_was_ignored(
    uploading, tmp_path
):
    first = tmp_path / "first"
    second = tmp_path / "second"

    uploading(uploads_dir=first)

    with pytest.warns(UserWarning, match=r"uploads_dir=.* is ignored"):
        client = uploading(uploads_dir=second)

    assert upload_module.UPLOADS_DIR == first
    assert send(client, "a.txt", b"hello").status_code == 200
    assert names_in(second) == []
    assert len(names_in(first)) == 1


def test_a_later_router_asking_for_another_returns_dir_is_told_it_was_ignored(
    returning, tmp_path
):
    first = tmp_path / "first"
    second = tmp_path / "second"

    returning(returns_dir=first)

    with pytest.warns(UserWarning, match=r"returns_dir=.* is ignored"):
        client = returning(returns_dir=second)

    assert returned_files.RETURNS_DIR == first

    result = client.post("/bundle/invoke", json={}).json()["result"]

    assert names_in(second) == []
    assert names_in(first) == [result["value"]]


def test_two_routers_with_the_same_directory_settle_it_silently(uploading,
                                                                 tmp_path):
    # filterwarnings=error, so a warning here would fail the test.
    same = tmp_path / "same"

    uploading(uploads_dir=same)
    uploading(uploads_dir=str(same))

    assert upload_module.UPLOADS_DIR == same


def test_one_piece_of_prose_covers_the_directory_and_the_ttl(uploading,
                                                              tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    with pytest.warns(UserWarning) as records:
        uploading(uploads_dir=first, pending_ttl=3600)
        uploading(uploads_dir=second, pending_ttl=60)

    said = [str(record.message) for record in records]

    assert len(said) == 2
    assert skeleton(said[0], "uploads_dir", second, first) == skeleton(
        said[1], "pending_ttl", 60, 3600
    )


def test_the_effective_directory_is_the_one_cut_out_of_a_message(uploading,
                                                                  tmp_path):
    custom = tmp_path / "custom-uploads"

    uploading(uploads_dir=custom)

    text = f"table: not an accepted file type: {str(custom / 'notes.bin')!r}"
    cut = without_storage_paths(text)

    assert cut == "table: not an accepted file type: 'notes.bin'"
    assert not carries(cut, custom)


def test_the_effective_returns_directory_is_cut_out_too(returning, tmp_path):
    custom = tmp_path / "custom-returns"

    returning(returns_dir=custom)

    text = f"table: not an accepted file type: {str(custom / 'r.bin')!r}"
    cut = without_storage_paths(text)

    assert cut == "table: not an accepted file type: 'r.bin'"
    assert not carries(cut, custom)


def test_a_custom_uploads_dir_serves_every_consumer(uploading, uploads_dir,
                                                    tmp_path):
    custom = tmp_path / "custom-uploads"
    client = uploading(uploads_dir=custom, pending_ttl=60)

    assert send(client, "a.txt", b"hello").status_code == 200
    assert send(client, "a.txt", b"other").status_code == 409

    invoked = client.post("/read/invoke", json={"document": "a.txt"})
    prefilled = client.get("/read/",
                           params={"prefill": json.dumps({"document":
                                                          "a.txt"})})

    assert invoked.status_code == 200
    assert invoked.json()["result"]["value"] == "hello"
    assert prefilled.status_code == 200
    assert (custom / "a.txt").is_file()
    assert upload_module.reference_of(str(custom / "a.txt")) == "a.txt"

    expired = custom / pending_of("gone.txt", now() - 120)
    expired.write_bytes(b"old")

    upload_module.sweep()

    assert not expired.exists()
    assert names_in(custom) == ["a.txt"]
    assert names_in(uploads_dir) == []


def test_a_custom_uploads_dir_never_reaches_the_client(uploading, tmp_path):
    custom = tmp_path / "custom-uploads"
    client = uploading(uploads_dir=custom)

    assert send(client, "notes.bin", b"nope").status_code == 200

    refused = client.post("/read/invoke", json={"document": "notes.bin"})
    prefilled = client.get("/read/",
                           params={"prefill": json.dumps({"document":
                                                          "notes.bin"})})

    assert refused.status_code == 422
    assert "not an accepted file type: 'notes.bin'" in refused.json()["error"]
    assert not carries(refused.text, custom)
    assert prefilled.status_code == 400
    assert not carries(prefilled.text, custom)


def test_a_custom_returns_dir_serves_every_consumer(returning, returns_dir,
                                                    tmp_path):
    custom = tmp_path / "custom-returns"
    client = returning(returns_dir=custom, returns_ttl=60)
    result = client.post("/bundle/invoke", json={}).json()["result"]
    fetched = client.get(f"/returns/{result['value']}")

    assert names_in(custom) == [result["value"]]
    assert fetched.status_code == 200
    assert fetched.content == b"xxxx"
    assert fetched.headers["content-disposition"].endswith('"r.bin"')

    dated = stamped_of("gone.bin", now() - 120, RETURNS_MARKER)
    expired = custom / f"{'0' * 32}.{dated}"
    expired.write_bytes(b"old")

    returned_files.sweep()

    assert not expired.exists()
    assert names_in(custom) == [result["value"]]
    assert names_in(returns_dir) == []
