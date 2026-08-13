import os
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import pytest

import func_to_web.web.execution as execution_module
import func_to_web.web.upload as upload_module
from func_to_web import FileHint
from func_to_web.web.references import stored_of
from func_to_web.web.upload import reference_of

TxtFile = Annotated[str, FileHint(extensions=(".txt",))]
AnyFile = Annotated[str, FileHint()]


@dataclass
class Box:
    document: TxtFile
    tag: str = "t"


@dataclass
class Card:
    note: str = "n"


def resolve(reference):
    return upload_module.stored_file(reference)


def snapshot_of(directory):
    return {entry.name: entry.read_bytes()
            for entry in sorted(directory.iterdir()) if entry.is_file()}


def symlink_or_skip(link, target, target_is_directory=False):
    try:
        os.symlink(target, link, target_is_directory=target_is_directory)
    except (OSError, NotImplementedError, AttributeError):
        pytest.skip("this platform does not allow creating symlinks")


@pytest.fixture
def resolver_calls(monkeypatch):
    calls = []
    original = upload_module.stored_file

    def spy(reference):
        result = original(reference)
        calls.append((reference, result))
        return result

    monkeypatch.setattr(execution_module, "stored_file", spy)

    return calls


def test_stored_reference_resolves_to_its_path(stored_file, uploads_dir):
    stored_file("a.txt", data=b"body")

    assert resolve("a.txt") == str((uploads_dir / "a.txt").resolve())


def test_missing_reference_raises_file_not_found(uploads_dir):
    with pytest.raises(FileNotFoundError, match="File not found: nope.txt"):
        resolve("nope.txt")


def test_reference_deleted_after_upload_raises_file_not_found(stored_file,
                                                              uploads_dir):
    stored_file("a.txt")

    assert resolve("a.txt")

    (uploads_dir / "a.txt").unlink()

    with pytest.raises(FileNotFoundError):
        resolve("a.txt")


def test_directory_is_not_a_resolvable_file(uploads_dir):
    (uploads_dir / "folder").mkdir()

    with pytest.raises(FileNotFoundError):
        resolve("folder")


def test_file_inside_a_subdirectory_is_refused(uploads_dir):
    nested = uploads_dir / "folder"
    nested.mkdir()
    (nested / "a.txt").write_bytes(b"body")

    with pytest.raises(ValueError, match="storage directory"):
        resolve("folder/a.txt")


def test_symlink_pointing_inside_storage_resolves_to_its_target(stored_file,
                                                                uploads_dir):
    stored_file("real.txt", data=b"body")
    symlink_or_skip(uploads_dir / "link.txt", uploads_dir / "real.txt")

    assert resolve("link.txt") == str((uploads_dir / "real.txt").resolve())


def test_symlink_escaping_storage_is_refused(sized_file, uploads_dir):
    outside = sized_file("secret.txt", data=b"secret")
    symlink_or_skip(uploads_dir / "link.txt", outside)

    with pytest.raises(ValueError, match="storage directory"):
        resolve("link.txt")


def test_symlink_to_a_directory_is_refused(tmp_path, uploads_dir):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    symlink_or_skip(uploads_dir / "link", elsewhere, target_is_directory=True)

    with pytest.raises((ValueError, FileNotFoundError)):
        resolve("link")


@pytest.mark.parametrize("reference", ["../a.txt", "..\\a.txt", "../../a.txt"])
def test_traversal_reference_is_refused(uploads_dir, reference):
    (uploads_dir.parent / "a.txt").write_bytes(b"outside")

    with pytest.raises(ValueError, match="invalid file reference"):
        resolve(reference)


def test_bare_dotdot_is_refused(uploads_dir):
    with pytest.raises(ValueError, match="invalid file reference"):
        resolve("..")


def test_empty_reference_is_refused(uploads_dir):
    with pytest.raises(ValueError, match="must be a file name"):
        resolve("")


def test_absolute_reference_outside_storage_is_refused(sized_file):
    outside = sized_file("secret.txt", data=b"secret")

    with pytest.raises(ValueError, match="storage directory"):
        resolve(str(outside))


def test_absolute_reference_inside_storage_is_refused(stored_file,
                                                      uploads_dir):
    stored_file("a.txt", data=b"body")
    contained = str((uploads_dir / "a.txt").resolve())

    with pytest.raises(ValueError, match="storage directory"):
        resolve(contained)


def test_a_contained_path_is_not_a_reference(stored_file, uploads_dir):
    stored_file("a.txt", data=b"body")

    for contained in ("./a.txt", "sub/../a.txt", ".\\a.txt"):
        with pytest.raises(ValueError, match="storage directory"):
            resolve(contained)


def test_the_bare_name_of_a_stored_file_is_its_reference(stored_file,
                                                         uploads_dir):
    stored_file("a.txt", data=b"body")

    assert reference_of(str(uploads_dir / "a.txt")) == "a.txt"
    assert resolve(reference_of(str(uploads_dir / "a.txt"))) == str(
        (uploads_dir / "a.txt").resolve())


def test_a_path_outside_the_storage_has_no_reference(sized_file):
    assert reference_of(str(sized_file("loose.txt"))) is None


def test_a_pending_name_has_no_reference(uploads_dir, pending_file):
    pending = pending_file("a.txt")

    assert reference_of(str(pending)) is None


def test_a_symlink_inside_storage_keeps_its_own_name(stored_file, uploads_dir):
    stored_file("real.txt", data=b"body")
    symlink_or_skip(uploads_dir / "link.txt", uploads_dir / "real.txt")

    reference = reference_of(str(uploads_dir / "link.txt"))

    assert reference == "link.txt"
    assert resolve(reference) == str((uploads_dir / "real.txt").resolve())


def test_a_symlink_escaping_storage_has_no_reference(sized_file, uploads_dir):
    outside = sized_file("secret.txt", data=b"secret")
    symlink_or_skip(uploads_dir / "escape.txt", outside)

    assert reference_of(str(uploads_dir / "escape.txt")) is None


@pytest.mark.parametrize("name", ["a.txt", "a.bin", "a.EXE", "a", "a.tar.gz"])
def test_extension_does_not_influence_resolution(stored_file, uploads_dir,
                                                 name):
    stored_file(name, data=b"body")

    assert resolve(name) == str((uploads_dir / name).resolve())


def test_empty_file_resolves(stored_file, uploads_dir):
    stored_file("empty.txt", data=b"")

    assert resolve("empty.txt") == str((uploads_dir / "empty.txt").resolve())


def test_result_is_a_plain_str(stored_file):
    stored_file("a.txt")

    result = resolve("a.txt")

    assert type(result) is str
    assert not isinstance(result, Path)


def test_resolution_creates_no_file(stored_file, uploads_dir):
    stored_file("a.txt")
    before = snapshot_of(uploads_dir)

    resolve("a.txt")

    for reference in ("nope.txt", "../a.txt", "", ".."):
        with pytest.raises((ValueError, FileNotFoundError)):
            resolve(reference)

    assert snapshot_of(uploads_dir) == before


def test_resolution_does_not_modify_contents(stored_file, uploads_dir):
    stored_file("a.txt", data=b"payload")
    target = uploads_dir / "a.txt"
    before = target.stat().st_mtime_ns

    resolve("a.txt")

    assert target.read_bytes() == b"payload"
    assert target.stat().st_mtime_ns == before


@pytest.mark.parametrize("name", ["a.txt", "b.bin", "c"])
def test_result_always_lives_inside_the_storage_directory(stored_file,
                                                          uploads_dir, name):
    stored_file(name)

    result = Path(resolve(name))

    assert result.parent == uploads_dir.resolve()
    assert result.is_file()


def test_stored_of_accepts_a_contained_name(uploads_dir):
    (uploads_dir / "a.txt").write_bytes(b"body")

    assert stored_of("a.txt", uploads_dir) == (uploads_dir / "a.txt").resolve()


def test_stored_of_does_not_require_the_file_to_exist(uploads_dir):
    assert stored_of("ghost.txt", uploads_dir) == (
        uploads_dir / "ghost.txt").resolve()


@pytest.mark.parametrize("reference", ["", "../a.txt", "sub/a.txt"])
def test_stored_of_refuses_what_leaves_the_root(uploads_dir, reference):
    with pytest.raises(ValueError):
        stored_of(reference, uploads_dir)


def test_stored_of_returns_a_path(uploads_dir):
    assert isinstance(stored_of("a.txt", uploads_dir), Path)


def test_resolver_reaches_a_plain_file_field(client_factory, stored_file,
                                             uploads_dir, resolver_calls):
    stored_file("a.txt", data=b"body")
    captured = []

    def keep(document: TxtFile) -> str:
        captured.append(document)
        return "ok"

    client = client_factory(keep)
    response = client.post("/keep/invoke", json={"document": "a.txt"})

    assert response.status_code == 200
    assert captured == [str((uploads_dir / "a.txt").resolve())]
    assert [reference for reference, _ in resolver_calls] == ["a.txt"]


def test_resolver_reaches_an_optional_file_field(client_factory, stored_file,
                                                 uploads_dir, resolver_calls):
    stored_file("a.txt", data=b"body")
    captured = []

    def keep(document: TxtFile | None = None) -> str:
        captured.append(document)
        return "ok"

    client = client_factory(keep)
    response = client.post("/keep/invoke", json={"document": "a.txt"})

    assert response.status_code == 200
    assert captured == [str((uploads_dir / "a.txt").resolve())]
    assert [reference for reference, _ in resolver_calls] == ["a.txt"]


def test_resolver_never_sees_a_null_optional(client_factory, resolver_calls):
    captured = []

    def keep(document: TxtFile | None = None) -> str:
        captured.append(document)
        return "ok"

    client = client_factory(keep)
    response = client.post("/keep/invoke", json={"document": None})

    assert response.status_code == 200
    assert captured == [None]
    assert resolver_calls == []


def test_resolver_reaches_every_item_of_a_list(client_factory, stored_file,
                                               uploads_dir, resolver_calls):
    stored_file("a.txt", data=b"one")
    stored_file("b.txt", data=b"two")
    captured = []

    def keep(documents: list[TxtFile]) -> str:
        captured.append(documents)
        return "ok"

    client = client_factory(keep)
    response = client.post("/keep/invoke",
                           json={"documents": ["b.txt", "a.txt", "b.txt"]})

    assert response.status_code == 200
    assert captured == [[str((uploads_dir / name).resolve())
                         for name in ("b.txt", "a.txt", "b.txt")]]
    assert [reference for reference, _ in resolver_calls] == [
        "b.txt", "a.txt", "b.txt"]


def test_resolver_skips_the_nulls_of_a_list(client_factory, stored_file,
                                            uploads_dir, resolver_calls):
    stored_file("a.txt", data=b"one")
    stored_file("b.txt", data=b"two")
    captured = []

    def keep(documents: list[TxtFile | None]) -> str:
        captured.append(documents)
        return "ok"

    client = client_factory(keep)
    response = client.post("/keep/invoke",
                           json={"documents": ["a.txt", None, "b.txt"]})

    assert response.status_code == 200
    assert captured == [[str((uploads_dir / "a.txt").resolve()), None,
                         str((uploads_dir / "b.txt").resolve())]]
    assert [reference for reference, _ in resolver_calls] == ["a.txt", "b.txt"]


def test_resolver_skips_the_non_file_branch_of_a_list(client_factory,
                                                      stored_file, uploads_dir,
                                                      resolver_calls):
    stored_file("a.txt", data=b"one")
    stored_file("b.txt", data=b"two")
    captured = []

    def keep(documents: list[TxtFile | int]) -> str:
        captured.append(documents)
        return "ok"

    client = client_factory(keep)
    response = client.post("/keep/invoke",
                           json={"documents": ["a.txt", 3, "b.txt"]})

    assert response.status_code == 200
    assert captured == [[str((uploads_dir / "a.txt").resolve()), 3,
                         str((uploads_dir / "b.txt").resolve())]]
    assert [reference for reference, _ in resolver_calls] == ["a.txt", "b.txt"]


def test_resolver_reaches_a_nested_list(client_factory, stored_file,
                                        uploads_dir, resolver_calls):
    for name in ("a.txt", "b.txt", "c.txt"):
        stored_file(name, data=name.encode())

    captured = []

    def keep(documents: list[list[TxtFile]]) -> str:
        captured.append(documents)
        return "ok"

    client = client_factory(keep)
    response = client.post(
        "/keep/invoke",
        json={"documents": [["a.txt"], ["b.txt", "c.txt"]]})

    assert response.status_code == 200
    assert captured == [[[str((uploads_dir / "a.txt").resolve())],
                         [str((uploads_dir / "b.txt").resolve()),
                          str((uploads_dir / "c.txt").resolve())]]]
    assert [reference for reference, _ in resolver_calls] == [
        "a.txt", "b.txt", "c.txt"]


def test_resolver_reaches_a_dataclass_field(client_factory, stored_file,
                                            uploads_dir, resolver_calls):
    stored_file("a.txt", data=b"body")
    captured = []

    def keep(row: Box) -> str:
        captured.append(row)
        return "ok"

    client = client_factory(keep)
    response = client.post("/keep/invoke",
                           json={"row": {"document": "a.txt", "tag": "z"}})

    assert response.status_code == 200
    assert captured == [Box(str((uploads_dir / "a.txt").resolve()), "z")]
    assert [reference for reference, _ in resolver_calls] == ["a.txt"]


def test_resolver_reaches_a_list_of_dataclasses(client_factory, stored_file,
                                                uploads_dir, resolver_calls):
    stored_file("a.txt", data=b"one")
    stored_file("b.txt", data=b"two")
    captured = []

    def keep(rows: list[Box]) -> str:
        captured.append(rows)
        return "ok"

    client = client_factory(keep)
    response = client.post(
        "/keep/invoke",
        json={"rows": [{"document": "b.txt"}, {"document": "a.txt"}]})

    assert response.status_code == 200
    assert captured == [[Box(str((uploads_dir / "b.txt").resolve())),
                         Box(str((uploads_dir / "a.txt").resolve()))]]
    assert [reference for reference, _ in resolver_calls] == ["b.txt", "a.txt"]


# A union whose options share one runtime type keeps the discriminated
# wrapper the browser sends, and the walk has to descend through it: the
# resolver is owed the files of the branch $type names, and owed nothing at
# all on any other. test_transport.py pins what each shape means; these four
# pin which nodes the resolver is handed.
def test_resolver_reaches_inside_the_branch_a_wrapper_names(client_factory,
                                                            stored_file,
                                                            uploads_dir,
                                                            resolver_calls):
    stored_file("a.txt", data=b"one")
    stored_file("b.txt", data=b"two")
    captured = []

    def keep(items: list[TxtFile] | list[int]) -> str:
        captured.append(items)
        return "ok"

    client = client_factory(keep)
    response = client.post(
        "/keep/invoke",
        json={"items": {"$type": "list[str]", "$value": ["a.txt", "b.txt"]}})

    assert response.status_code == 200
    assert captured == [[str((uploads_dir / name).resolve())
                         for name in ("a.txt", "b.txt")]]
    assert [reference for reference, _ in resolver_calls] == ["a.txt", "b.txt"]


def test_resolver_never_sees_the_branch_a_wrapper_does_not_name(
        client_factory, stored_file, resolver_calls):
    stored_file("a.txt")
    captured = []

    def keep(items: list[TxtFile] | list[int]) -> str:
        captured.append(items)
        return "ok"

    client = client_factory(keep)
    response = client.post("/keep/invoke",
                           json={"items": {"$type": "list[int]",
                                           "$value": [1, 2]}})

    assert response.status_code == 200
    assert captured == [[1, 2]]
    assert resolver_calls == []


def test_resolver_reaches_the_file_of_the_inline_class_that_is_named(
        client_factory, stored_file, uploads_dir, resolver_calls):
    stored_file("a.txt", data=b"body")
    captured = []

    def keep(row: Box | Card) -> str:
        captured.append(row)
        return "ok"

    client = client_factory(keep)
    response = client.post(
        "/keep/invoke",
        json={"row": {"$type": "Box", "document": "a.txt", "tag": "z"}})

    assert response.status_code == 200
    assert captured == [Box(str((uploads_dir / "a.txt").resolve()), "z")]
    assert [reference for reference, _ in resolver_calls] == ["a.txt"]


def test_resolver_never_sees_the_inline_class_that_is_not_named(
        client_factory, resolver_calls):
    # A reference that resolves to nothing proves it: the field of the class
    # $type names is a plain str, so the walk stops before the resolver, and
    # the call runs on a name no storage would have found.
    captured = []

    def keep(row: Box | Card) -> str:
        captured.append(row)
        return "ok"

    client = client_factory(keep)
    response = client.post("/keep/invoke",
                           json={"row": {"$type": "Card", "note": "ghost.txt"}})

    assert response.status_code == 200
    assert captured == [Card("ghost.txt")]
    assert resolver_calls == []


def test_resolver_is_not_called_for_a_plain_string_field(client_factory,
                                                         stored_file,
                                                         resolver_calls):
    stored_file("a.txt")

    def keep(note: str) -> str:
        return note

    client = client_factory(keep)
    response = client.post("/keep/invoke", json={"note": "a.txt"})

    assert response.status_code == 200
    assert resolver_calls == []


def test_resolver_failure_stops_the_call(client_factory, resolver_calls):
    called = []

    def keep(document: TxtFile) -> str:
        called.append(document)
        return "ok"

    client = client_factory(keep)
    response = client.post("/keep/invoke", json={"document": "ghost.txt"})

    assert response.status_code == 422
    assert response.json() == {
        "error": "FileNotFoundError: File not found: ghost.txt"
    }
    assert called == []


def test_traversal_through_invoke_reports_the_storage_rule(client_factory):
    def keep(document: AnyFile) -> str:
        return document

    client = client_factory(keep)
    response = client.post("/keep/invoke", json={"document": "../evil.txt"})

    assert response.status_code == 422
    assert response.json()["error"] == (
        "ValueError: invalid file reference '../evil.txt': "
        "is not a file of the storage directory"
    )


def test_function_receives_a_readable_path(client_factory, stored_file):
    stored_file("a.txt", data=b"hello")

    def keep(document: TxtFile) -> str:
        return Path(document).read_text(encoding="utf-8")

    client = client_factory(keep)
    response = client.post("/keep/invoke", json={"document": "a.txt"})

    assert response.status_code == 200
    assert response.json()["result"]["value"] == "hello"
