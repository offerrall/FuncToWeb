from pathlib import Path
from typing import Annotated, Any, Optional, Union

import pytest

from func_to_web import Download, OpenForm, ReturnContractError, WebFunction
from func_to_web.web import references
from func_to_web.web.references import (
    FILENAME_LIMIT,
    PENDING_MARKER,
    segment_of,
)
from shared import carries

FORBIDDEN = 'cannot contain any of <>:"|?*'

REFUSED_NAMES = (
    [(f"a{character}b.txt", FORBIDDEN) for character in '<>:"|?*']
    + [(name, "is a reserved device name")
       for name in ("NUL", "nul.txt", "CON", "COM1.log", "LPT9", "aux")]
    + [(name, "cannot end with a dot or a space")
       for name in ("report.txt.", "report.txt ", "report ")]
    + [(f"a{character}b.txt", "cannot contain a control character")
       for character in ("\x00", "\n", "\r", "\x1f")]
    + [(name, "cannot contain separators")
       for name in ("sub/a.txt", "sub\\a.txt", "/reports/a.txt")]
    + [(name, "must be a file name") for name in ("", ".", "..", "...")]
    + [(f"{PENDING_MARKER}a.txt",
        f"cannot start with the reserved prefix '{PENDING_MARKER}'")]
)

# Agent A is adding the returns counterpart of PENDING_MARKER to
# web.references; the name it will carry is not settled, so it is looked up
# instead of spelled out.
RETURNS_MARKER = next(
    (value for name, value in vars(references).items()
     if "MARKER" in name and name != "PENDING_MARKER" and type(value) is str),
    None,
)


def returning(annotation, value=None):
    def produce():
        return value

    produce.__annotations__["return"] = annotation

    return produce


def parser_for(annotation):
    return WebFunction(returning(annotation)).return_parser


def resolved(annotation, value):
    parser = WebFunction(returning(annotation, value)).return_parser

    return parser.resolved(value)


def named(files):
    return [item.filename for item in files]


def target(product_id: int = 1) -> str:
    return "updated"


def exploding(value, index):
    raise RuntimeError("no name")


def numbered(value, index):
    return f"file-{index}.bin"


@pytest.fixture
def invoke(client_factory):
    def call(annotation, value):
        client = client_factory(returning(annotation, value))

        return client.post("/produce/invoke", json={})

    return call


def test_a_function_without_a_return_annotation_has_no_parser():
    def produce():
        return 1

    assert WebFunction(produce).return_parser is None


@pytest.mark.parametrize("annotation", [
    None,
    int,
    str,
    dict,
    Path,
    bytes,
    Any,
    list,
    list[str],
    list[Path],
    list[list[Path]],
    tuple[str, int],
    tuple[Path, ...],
    tuple[()],
    dict[str, Path],
    str | None,
    Path | str,
    Optional[Path],
    Annotated[Path, "not a mark"],
])
def test_an_ordinary_return_has_no_parser(annotation):
    assert parser_for(annotation) is None


def test_a_download_path_becomes_a_file_named_after_its_basename():
    file = resolved(Annotated[Path, Download()], Path("reports/june.pdf"))

    assert (file.source, file.filename) == (Path("reports/june.pdf"),
                                            "june.pdf")


def test_a_download_str_is_read_as_a_path():
    file = resolved(Annotated[str, Download()], "reports/june.pdf")

    assert (file.source, file.filename) == (Path("reports/june.pdf"),
                                            "june.pdf")


def test_download_bytes_are_kept_in_memory_under_a_fixed_filename():
    file = resolved(Annotated[bytes, Download(filename="june.pdf")], b"data")

    assert (file.source, file.filename) == (b"data", "june.pdf")


def test_an_optional_download_accepts_the_file():
    file = resolved(Annotated[Path, Download()] | None, Path("june.pdf"))

    assert file.filename == "june.pdf"


def test_an_optional_download_accepts_none():
    assert resolved(Annotated[Path, Download()] | None, None) is None


def test_an_optional_download_written_with_union_accepts_none():
    assert resolved(Union[Annotated[Path, Download()], None], None) is None


def test_a_download_list_keeps_the_returned_order():
    files = resolved(Annotated[list[Path], Download()],
                     [Path("c.txt"), Path("a.txt"), Path("b.txt")])

    assert named(files) == ["c.txt", "a.txt", "b.txt"]


def test_a_variadic_download_tuple_yields_one_file_per_element():
    files = resolved(Annotated[tuple[Path, ...], Download()],
                     (Path("a.txt"), Path("b.txt")))

    assert named(files) == ["a.txt", "b.txt"]


def test_a_positional_download_tuple_yields_one_file_per_position():
    files = resolved(Annotated[tuple[Path, str], Download()],
                     (Path("a.txt"), "dir/b.txt"))

    assert named(files) == ["a.txt", "b.txt"]


def test_nested_download_lists_are_flattened_in_order():
    files = resolved(Annotated[list[list[Path]], Download()],
                     [[Path("a.txt"), Path("b.txt")], [Path("c.txt")]])

    assert named(files) == ["a.txt", "b.txt", "c.txt"]


def test_nested_download_tuples_are_flattened_in_order():
    files = resolved(
        Annotated[tuple[tuple[Path, str], tuple[Path, ...]], Download()],
        ((Path("a.txt"), "b.txt"), (Path("c.txt"),)),
    )

    assert named(files) == ["a.txt", "b.txt", "c.txt"]


def test_a_download_union_of_file_types_accepts_any_of_them():
    file = resolved(Annotated[Path | str | bytes, Download(filename="a.bin")],
                    b"data")

    assert (file.source, file.filename) == (b"data", "a.bin")


def test_other_metadata_inside_a_download_is_ignored():
    files = resolved(Annotated[list[Annotated[Path, "a note"]], Download()],
                     [Path("a.txt")])

    assert named(files) == ["a.txt"]


def test_an_empty_tuple_download_still_accepts_files():
    files = resolved(Annotated[tuple[()], Download()], (Path("a.txt"),))

    assert named(files) == ["a.txt"]


def test_a_fixed_filename_renames_a_single_file():
    file = resolved(Annotated[Path, Download(filename="renamed.txt")],
                    Path("original.txt"))

    assert file.filename == "renamed.txt"


def test_a_fixed_filename_renames_a_one_element_collection():
    files = resolved(Annotated[list[Path], Download(filename="renamed.txt")],
                     [Path("original.txt")])

    assert named(files) == ["renamed.txt"]


def test_a_filename_callable_receives_each_value_and_its_index():
    seen = []

    def record(value, index):
        seen.append((value, index))

        return f"{index}.txt"

    resolved(Annotated[list[Path], Download(filename=record)],
             [Path("a.txt"), Path("b.txt"), Path("c.txt")])

    assert seen == [(Path("a.txt"), 0), (Path("b.txt"), 1), (Path("c.txt"), 2)]


def test_a_filename_callable_names_every_file_it_produces():
    files = resolved(Annotated[list[bytes], Download(filename=numbered)],
                     [b"one", b"two"])

    assert named(files) == ["file-0.bin", "file-1.bin"]


def test_each_download_restarts_its_own_indexes():
    files = resolved(
        tuple[
            Annotated[list[Path], Download(filename=lambda value, index:
                                           f"first-{index}.txt")],
            Annotated[list[Path], Download(filename=lambda value, index:
                                           f"second-{index}.txt")],
        ],
        ([Path("a.txt"), Path("b.txt")], [Path("c.txt")]),
    )

    assert [named(group) for group in files] == [
        ["first-0.txt", "first-1.txt"],
        ["second-0.txt"],
    ]


def test_a_download_inside_a_tuple_leaves_the_other_positions_untouched():
    first, second = resolved(tuple[str, Annotated[Path, Download()]],
                             ("Finished", Path("a.txt")))

    assert (first, second.filename) == ("Finished", "a.txt")


def test_a_download_marked_element_is_resolved_for_every_list_item():
    files = resolved(list[Annotated[Path, Download()]],
                     [Path("a.txt"), Path("b.txt")])

    assert named(files) == ["a.txt", "b.txt"]


def test_an_optional_download_inside_a_tuple_accepts_none():
    assert resolved(tuple[Annotated[Path, Download()] | None, str],
                    (None, "Finished")) == (None, "Finished")


def test_an_empty_download_collection_resolves_to_no_files():
    assert resolved(Annotated[list[Path], Download()], []) == []


@pytest.mark.parametrize("annotation, message", [
    (Annotated[Path, Download(), Download()],
     "an Annotated cannot carry more than one Download"),
    (Annotated[list[Annotated[Path, Download()]], Download()],
     "a Download cannot contain another Download"),
    (Annotated[tuple[Annotated[Path, Download()], str], Download()],
     "a Download cannot contain another Download"),
    (Annotated[int, Download()],
     "a Download supports Path, str or bytes, not int"),
    (Annotated[dict, Download()],
     "a Download supports Path, str or bytes, not dict"),
    (Annotated[Any, Download()],
     "a Download supports Path, str or bytes, not Any"),
    (Annotated[list, Download()],
     "a Download supports Path, str or bytes, not list"),
    (Annotated[list[int], Download()],
     "a Download supports Path, str or bytes, not int"),
    (Annotated[Path | None, Download()],
     "None is not allowed inside a Download; it can replace a whole Download "
     "return, not one of its files"),
    (Annotated[list[Path | None], Download()],
     "None is not allowed inside a Download; it can replace a whole Download "
     "return, not one of its files"),
    (Annotated[tuple[Path, None], Download()],
     "a Download supports Path, str or bytes, not None"),
    (Annotated[list[Path] | Path, Download()],
     "a union inside a Download can only mix Path, str and bytes"),
    (Annotated[Path, Download()] | str,
     "a union cannot mix Download and ordinary return branches"),
    (str | Annotated[Path, Download()],
     "a union cannot mix Download and ordinary return branches"),
    (Annotated[list[Path], Download()] | dict,
     "a union cannot mix Download and ordinary return branches"),
    (Annotated[Path, Download()] | Annotated[bytes, Download(filename="a")],
     "a union cannot carry more than one Download branch"),
    (Annotated[Path, Download()] | list[Annotated[str, Download()]] | None,
     "a union cannot carry more than one Download branch"),
])
def test_an_impossible_download_is_rejected_when_the_function_is_prepared(
    annotation,
    message,
):
    with pytest.raises(ReturnContractError) as error:
        parser_for(annotation)

    assert str(error.value) == message


def test_an_invalid_filename_type_is_rejected_by_the_mark_itself():
    with pytest.raises(TypeError) as error:
        Download(filename=5)

    assert str(error.value) == (
        "Download.filename must be str, a callable or None, got int"
    )


@pytest.mark.parametrize("annotation, value, message", [
    (Annotated[Path, Download()], "a.txt",
     "expected Path for Download, got str"),
    (Annotated[bytes, Download(filename="a.bin")], Path("a.txt"),
     "expected bytes for Download, got Path"),
    (Annotated[bytes, Download(filename="a.bin")], bytearray(b"data"),
     "expected bytes for Download, got bytearray"),
    (Annotated[Path | str, Download()], 5,
     "expected Path or str for Download, got int"),
    (Annotated[list[Path], Download()], Path("a.txt"),
     "expected a list or tuple of files for Download, got Path"),
    (Annotated[list[Path], Download()], "a.txt",
     "expected a list or tuple of files for Download, got str"),
    (Annotated[tuple[Path, str], Download()], Path("a.txt"),
     "expected 2 files for Download, got Path"),
    (Annotated[tuple[Path, str], Download()], (Path("a.txt"),),
     "expected 2 files for Download, got 1"),
    (Annotated[Path, Download()], None,
     "None is not allowed for this Download return"),
    (list[Annotated[Path, Download()]], Path("a.txt"),
     "expected a list or tuple of return elements, got Path"),
    (tuple[Annotated[Path, Download()], str], "a.txt",
     "expected 2 return elements, got str"),
    (tuple[Annotated[Path, Download()], str], (Path("a.txt"),),
     "expected 2 return elements, got 1"),
    (tuple[Annotated[Path, Download()], str], (Path("a.txt"), "x", "y"),
     "expected 2 return elements, got 3"),
])
def test_a_returned_shape_that_breaks_the_contract_fails_the_invocation(
    invoke,
    annotation,
    value,
    message,
):
    response = invoke(annotation, value)

    assert response.status_code == 500
    assert response.json() == {"error": f"ReturnContractError: {message}"}


@pytest.mark.parametrize("annotation, value, message", [
    (Annotated[bytes, Download()], b"data",
     "bytes downloads require a filename"),
    (Annotated[Path, Download()], Path(""),
     "Download filename: must be a file name, got ''"),
    (Annotated[Path, Download()], Path(".."),
     "Download filename: must be a file name, got '..'"),
    (Annotated[Path, Download(filename=".")], Path("a.txt"),
     "Download filename: must be a file name, got '.'"),
    (Annotated[Path, Download(filename="")], Path("a.txt"),
     "Download filename: must be a file name, got ''"),
    (Annotated[Path, Download(filename="sub/a.txt")], Path("a.txt"),
     "Download filename: cannot contain separators, got 'sub/a.txt'"),
    (Annotated[Path, Download(filename="sub\\a.txt")], Path("a.txt"),
     r"Download filename: cannot contain separators, got 'sub\\a.txt'"),
    (Annotated[Path, Download(filename="/reports/a.txt")], Path("a.txt"),
     "Download filename: cannot contain separators, got '/reports/a.txt'"),
    (Annotated[list[Path], Download(filename="one.txt")],
     [Path("a.txt"), Path("b.txt")],
     "the fixed filename 'one.txt' would name 2 files; pass a callable "
     "filename instead"),
    (Annotated[Path, Download(filename=lambda value, index: 7)],
     Path("a.txt"),
     "Download filename callable returned an invalid value: expected str, "
     "got int"),
    (Annotated[Path, Download(filename=lambda value, index: "")],
     Path("a.txt"),
     "Download filename callable returned an invalid value: must be a file "
     "name, got ''"),
    (Annotated[Path, Download(filename=lambda value, index: "x/y.txt")],
     Path("a.txt"),
     "Download filename callable returned an invalid value: cannot contain "
     "separators, got 'x/y.txt'"),
    (Annotated[Path, Download(filename=exploding)], Path("a.txt"),
     "Download filename callable failed: RuntimeError: no name"),
])
def test_a_filename_that_breaks_the_contract_fails_the_invocation(
    invoke,
    annotation,
    value,
    message,
):
    response = invoke(annotation, value)

    assert response.status_code == 500
    assert response.json() == {"error": f"ReturnContractError: {message}"}


def test_a_failing_filename_callable_keeps_the_original_error_as_cause():
    with pytest.raises(ReturnContractError) as error:
        resolved(Annotated[Path, Download(filename=exploding)], Path("a.txt"))

    assert type(error.value.__cause__) is RuntimeError


@pytest.mark.parametrize("filename, reason", REFUSED_NAMES)
def test_a_filename_the_returns_route_would_refuse_breaks_the_contract(
    filename,
    reason,
):
    with pytest.raises(ReturnContractError) as error:
        resolved(Annotated[bytes, Download(filename=filename)], b"data")

    assert str(error.value) == f"Download filename: {reason}, got {filename!r}"


@pytest.mark.parametrize("filename, reason", [
    ("a<b.txt", 'cannot contain any of <>:"|?*'),
    ("NUL", "is a reserved device name"),
    ("report.txt ", "cannot end with a dot or a space"),
])
def test_a_produced_filename_obeys_the_same_rules(filename, reason):
    with pytest.raises(ReturnContractError) as error:
        resolved(Annotated[bytes, Download(filename=lambda value, index:
                                           filename)],
                 b"data")

    assert str(error.value) == (
        f"Download filename callable returned an invalid value: {reason}, "
        f"got {filename!r}"
    )


@pytest.mark.parametrize("filename, reason", [
    ("a|b.txt", 'cannot contain any of <>:"|?*'),
    ("com1.log", "is a reserved device name"),
    ("report.txt.", "cannot end with a dot or a space"),
])
def test_a_filename_taken_from_the_path_obeys_the_same_rules(filename, reason):
    with pytest.raises(ReturnContractError) as error:
        resolved(Annotated[Path, Download()], Path(filename))

    assert str(error.value) == f"Download filename: {reason}, got {filename!r}"


def test_a_filename_past_the_return_limit_breaks_the_contract():
    filename = "a" * (FILENAME_LIMIT + 1)

    with pytest.raises(ReturnContractError) as error:
        resolved(Annotated[bytes, Download(filename=filename)], b"data")

    assert str(error.value).startswith(
        f"Download filename: is longer than {FILENAME_LIMIT} bytes, got "
    )


def test_the_return_limit_is_measured_in_bytes_not_characters():
    filename = "é" * FILENAME_LIMIT

    assert len(filename) <= FILENAME_LIMIT
    assert len(filename.encode("utf-8")) > FILENAME_LIMIT

    with pytest.raises(ReturnContractError) as error:
        resolved(Annotated[bytes, Download(filename=filename)], b"data")

    assert f"is longer than {FILENAME_LIMIT} bytes" in str(error.value)


# The mirror of the "~p" rejection, for the marker that returns storage is
# gaining. The guard belongs to segment_of, so this only checks that the
# filename side inherits it; the skip fires while the constant is not there.
@pytest.mark.skipif(RETURNS_MARKER is None,
                    reason="no returns marker in web.references yet")
def test_a_filename_starting_with_the_returns_marker_is_rejected():
    filename = f"{RETURNS_MARKER}report.txt"

    with pytest.raises(ReturnContractError) as error:
        resolved(Annotated[bytes, Download(filename=filename)], b"data")

    assert str(error.value).startswith("Download filename: ")
    assert str(error.value).endswith(f"got {filename!r}")


@pytest.mark.parametrize("filename", [
    "report.txt",
    "a b;c=d.txt",
    ".hidden",
    "a-b_c.tar.gz",
    "file (1).txt",
    "informe-añejo.pdf",
    # A tilde is legal; what is reserved is a marker, and only its own two
    # characters. "~notes" is neither "~p" nor "~r".
    "~notes.txt",
    "a" * (FILENAME_LIMIT - 4) + ".pdf",
])
def test_a_filename_the_returns_route_accepts_is_kept(filename):
    file = resolved(Annotated[bytes, Download(filename=filename)], b"data")

    assert file.filename == filename
    assert segment_of(filename, FILENAME_LIMIT) == filename


def test_a_refused_filename_never_reaches_the_disk(invoke, tmp_path):
    response = invoke(Annotated[Path, Download()], tmp_path / "a<b.txt")

    assert response.status_code == 500
    assert response.json() == {
        "error": 'ReturnContractError: Download filename: cannot contain any '
                 'of <>:"|?*, got \'a<b.txt\''
    }
    assert not carries(response.json()["error"], tmp_path)


def test_a_refused_produced_filename_reports_no_local_path(invoke, tmp_path):
    source = tmp_path / "report.txt"
    annotation = Annotated[Path, Download(filename=lambda value, index:
                                          "NUL")]

    response = invoke(annotation, source)

    assert response.status_code == 500
    assert not carries(response.json()["error"], tmp_path)
    assert not carries(response.json()["error"], source)


def test_a_self_containing_collection_fails_against_the_declared_files():
    recursive = []
    recursive.append(recursive)

    with pytest.raises(ReturnContractError) as error:
        resolved(Annotated[list[Path], Download()], recursive)

    assert str(error.value) == "expected Path for Download, got list"


def test_a_resolved_download_is_offered_as_a_file(invoke, sized_file):
    path = sized_file("report.txt", data=b"hello")

    response = invoke(Annotated[Path, Download()], path)

    assert response.status_code == 200
    assert response.json()["result"] == {
        "type": "download",
        "value": response.json()["result"]["value"],
        "filename": "report.txt",
    }


def test_several_resolved_downloads_reach_the_response_in_order(invoke,
                                                                sized_file):
    paths = [sized_file("a.txt"), sized_file("b.txt")]

    response = invoke(Annotated[list[Path], Download()], paths)

    assert response.status_code == 200
    assert [output["filename"] for output in response.json()["result"]] == [
        "a.txt",
        "b.txt",
    ]


def test_a_bytes_subclass_download_keeps_its_content_instead_of_a_path():
    class Blob(bytes):
        pass

    file = resolved(Annotated[bytes, Download(filename="a.bin")],
                    Blob(b"data"))

    assert file.source == b"data"


def test_a_str_subclass_download_takes_its_basename_like_any_str():
    class Reference(str):
        pass

    file = resolved(Annotated[str, Download()], Reference("reports/a.txt"))

    assert file.filename == "a.txt"


def test_open_form_marks_the_whole_return():
    parser = parser_for(Annotated[dict, OpenForm(target)])

    assert parser.form == OpenForm(target)
    assert parser.root is None


def test_open_form_leaves_the_returned_value_untouched():
    assert resolved(Annotated[dict, OpenForm(target)], {"a": 1}) == {"a": 1}


@pytest.mark.parametrize("annotation", [
    tuple[Annotated[dict, OpenForm(target)], str],
    list[Annotated[dict, OpenForm(target)]],
    Annotated[dict, OpenForm(target)] | None,
    Annotated[list[Annotated[dict, OpenForm(target)]], OpenForm(target)],
])
def test_open_form_cannot_mark_part_of_the_return(annotation):
    with pytest.raises(ReturnContractError) as error:
        parser_for(annotation)

    assert str(error.value) == (
        "OpenForm can only mark the whole return, and only once"
    )


def test_two_open_form_marks_on_the_same_annotated_are_rejected():
    with pytest.raises(ReturnContractError) as error:
        parser_for(Annotated[dict, OpenForm(target), OpenForm(target)])

    assert str(error.value) == (
        "an Annotated cannot carry more than one OpenForm"
    )


@pytest.mark.parametrize("annotation", [
    Annotated[dict, OpenForm(target), Download()],
    Annotated[Annotated[Path, Download()], OpenForm(target)],
    Annotated[tuple[Annotated[Path, Download()], str], OpenForm(target)],
    Annotated[list[Annotated[Path, Download()]], OpenForm(target)],
])
def test_open_form_cannot_be_combined_with_download(annotation):
    with pytest.raises(ReturnContractError) as error:
        parser_for(annotation)

    assert str(error.value) == "a return cannot mix OpenForm and Download"
