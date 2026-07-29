import os

from func_to_web.web.messages import without_storage_paths


def message_of(root, name):
    return f"table: not an accepted file type: {str(root / name)!r}"


def test_a_plain_path_loses_its_directory(uploads_dir):
    text = f"file does not exist: {uploads_dir}{os.sep}notes.bin"

    assert without_storage_paths(text) == "file does not exist: notes.bin"


def test_a_repr_escaped_path_loses_its_directory(uploads_dir):
    assert without_storage_paths(message_of(uploads_dir, "notes.bin")) == (
        "table: not an accepted file type: 'notes.bin'")


def test_the_returns_directory_is_cut_too(returns_dir):
    assert without_storage_paths(message_of(returns_dir, "r.pdf")) == (
        "table: not an accepted file type: 'r.pdf'")


def test_a_message_without_a_path_travels_unchanged():
    text = "File not found: nope.txt"

    assert without_storage_paths(text) == text


def test_every_occurrence_is_cut(uploads_dir):
    first = message_of(uploads_dir, "a.txt")
    second = message_of(uploads_dir, "b.txt")

    assert without_storage_paths(f"{first} and {second}") == (
        "table: not an accepted file type: 'a.txt' and "
        "table: not an accepted file type: 'b.txt'")


def test_the_comparison_folds_case(uploads_dir):
    if os.path.normcase("A") == "A":
        assert without_storage_paths(message_of(uploads_dir, "a.txt")) == (
            "table: not an accepted file type: 'a.txt'")

        return

    shouted = message_of(uploads_dir, "a.txt").upper()

    assert without_storage_paths(shouted) == (
        "TABLE: NOT AN ACCEPTED FILE TYPE: 'A.TXT'")


def test_the_file_name_itself_is_never_touched(uploads_dir):
    text = message_of(uploads_dir, "uploads")

    assert without_storage_paths(text) == (
        "table: not an accepted file type: 'uploads'")
