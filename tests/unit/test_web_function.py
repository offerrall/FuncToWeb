import re
from dataclasses import FrozenInstanceError, dataclass
from functools import partial
from typing import Annotated

import pytest
from pytypehint import Signature

from shared import TxtFile, carries
from func_to_web import (
    Download,
    OpenForm,
    ReturnContractError,
    SchemaValueError,
    WebFunction,
)
from func_to_web.models.function import RESERVED_SLUGS, SLUG_PATTERN


def add(a: int, b: int = 2) -> int:
    """Add two numbers."""
    return a + b


async def add_async(a: int, b: int = 2) -> int:
    """Add two numbers without blocking."""
    return a + b


def plain(a: int = 1) -> int:
    return a


def documented(a: int = 1) -> int:
    """First line.

    Second paragraph.
    """
    return a


def blur_image(a: int = 1) -> int:
    return a


def read_HTML_pages(a: int = 1) -> int:
    return a


def mi_informe(a: int = 1) -> int:
    return a


def save_result(a: int = 1) -> int:
    return a


def load__cache(a: int = 1) -> int:
    return a


def MyFunction(a: int = 1) -> int:
    return a


def __dunder__(a: int = 1) -> int:
    return a


def make_report(a: int = 1) -> Annotated[str, Download("report.txt")]:
    return "report.txt"


def open_add(a: int = 1) -> Annotated[dict, OpenForm(add)]:
    return {"a": a}


def unsupported_parameter(a: complex) -> int:
    return 1


def broken_return(a: int = 1) -> Annotated[int, Download()]:
    return 1


class CallableObject:
    def __call__(self, a: int = 1) -> int:
        return a


def title_of(html):
    return re.search(r"<title>(.*?)</title>", html).group(1)


def heading_of(html):
    return re.search(r"<h1>(.*?)</h1>", html).group(1)


def test_a_plain_function_builds():
    web_function = WebFunction(add)

    assert web_function.fn is add


def test_name_derives_from_dunder_name():
    assert WebFunction(add).name == "add"


def test_description_derives_from_the_docstring():
    assert WebFunction(add).description == "Add two numbers."


def test_a_multiline_docstring_is_normalized_but_keeps_its_line_breaks():
    assert WebFunction(documented).description == (
        "First line.\n\nSecond paragraph."
    )


def test_a_function_without_docstring_has_an_empty_description():
    assert WebFunction(plain).description == ""


def test_an_explicit_description_replaces_the_docstring():
    assert WebFunction(add, description="Explicit").description == "Explicit"


def test_an_explicit_description_is_also_normalized():
    assert WebFunction(add, description="  spaced  ").description == "spaced"


def test_an_empty_description_argument_still_derives():
    assert WebFunction(add, description="").description == "Add two numbers."


def test_a_blank_description_argument_blanks_a_docstring():
    web_function = WebFunction(add, description=" ")

    assert web_function.description == ""
    assert '<meta name="description"' not in web_function.html
    assert '<meta name="description"' in WebFunction(add).html


def test_an_explicit_name_replaces_the_derived_one():
    assert WebFunction(add, name="Account signup").name == "Account signup"


def test_the_name_is_stored_stripped():
    assert WebFunction(add, name="  Account  signup  ").name == (
        "Account  signup"
    )


@pytest.mark.parametrize(
    ("function", "expected"),
    [
        (save_result, "save_result"),
        (load__cache, "load__cache"),
        (__dunder__, "__dunder__"),
        (MyFunction, "MyFunction"),
        (blur_image, "blur_image"),
        (read_HTML_pages, "read_HTML_pages"),
    ],
)
def test_slug_derives_from_dunder_name(function, expected):
    assert WebFunction(function).slug == expected


def test_slug_derives_from_dunder_name_even_with_an_explicit_name():
    assert WebFunction(add, name="Account signup").slug == "add"


def test_an_explicit_slug_replaces_the_derived_one():
    assert WebFunction(add, slug="sum-two").slug == "sum-two"


def test_an_empty_slug_argument_still_derives():
    assert WebFunction(add, slug="").slug == "add"


def test_a_sync_function_is_served(client_factory):
    client = client_factory(add)

    response = client.post("/add/invoke", json={"a": 1, "b": 2})

    assert response.status_code == 200
    assert response.json() == {"result": {"type": "text", "value": "3"}}


def test_an_async_function_builds():
    web_function = WebFunction(add_async)

    assert web_function.slug == "add_async"
    assert web_function.description == "Add two numbers without blocking."


def test_an_async_function_is_awaited_when_served(client_factory):
    client = client_factory(add_async)

    response = client.post("/add_async/invoke", json={"a": 1, "b": 2})

    assert response.status_code == 200
    assert response.json() == {"result": {"type": "text", "value": "3"}}


def test_capture_prints_defaults_to_none():
    assert WebFunction(add).capture_prints is None


@pytest.mark.parametrize("value", [True, False])
def test_capture_prints_keeps_an_explicit_bool(value):
    assert WebFunction(add, capture_prints=value).capture_prints is value


def test_schema_is_a_signature():
    schema = WebFunction(add).schema

    assert isinstance(schema, Signature)
    assert [param.name for param in schema.params] == ["a", "b"]


def test_plan_is_a_dict_with_version_kind_and_fields():
    plan = WebFunction(add).plan

    assert type(plan) is dict
    assert plan["v"] == 1
    assert plan["kind"] == "form"
    assert [field["name"] for field in plan["fields"]] == ["a", "b"]


def test_html_embeds_the_compiled_plan(plan_of_page):
    web_function = WebFunction(add)

    assert plan_of_page(web_function.html) == web_function.plan


def test_the_embedded_plan_carries_the_metadata_name(plan_of_page):
    web_function = WebFunction(add, name="Account signup")

    assert plan_of_page(web_function.html)["name"] == "Account signup"


def test_the_plan_carries_the_metadata_name_and_description():
    web_function = WebFunction(add, name="Account signup",
                               description="Create an account")

    assert web_function.plan["name"] == "Account signup"
    assert web_function.plan["description"] == "Create an account"


def test_the_plan_falls_back_to_the_declared_metadata():
    web_function = WebFunction(add)

    assert web_function.plan["name"] == "add"
    assert web_function.plan["description"] == "Add two numbers."


def test_an_empty_description_travels_as_null_in_the_plan():
    def bare(a: int = 1) -> str:
        return "x"

    assert WebFunction(bare).plan["description"] is None


def test_the_metadata_does_not_reach_the_core_schema():
    web_function = WebFunction(add, name="Account signup",
                               description="Create an account")

    assert web_function.schema.name == "add"
    assert web_function.schema.doc == "Add two numbers."


def test_return_parser_is_none_without_marks():
    assert WebFunction(add).return_parser is None


def test_return_parser_is_built_for_a_download():
    parser = WebFunction(make_report).return_parser

    assert parser is not None
    assert parser.form is None
    assert parser.root is not None


def test_return_parser_is_built_for_an_open_form():
    parser = WebFunction(open_add).return_parser

    assert parser is not None
    assert parser.root is None
    assert parser.form == OpenForm(add)


@pytest.mark.parametrize(
    "field_name",
    [
        "fn",
        "name",
        "description",
        "slug",
        "capture_prints",
        "schema",
        "plan",
        "html",
        "return_parser",
    ],
)
def test_every_field_is_frozen(field_name):
    web_function = WebFunction(add)

    with pytest.raises(FrozenInstanceError):
        setattr(web_function, field_name, None)


def test_repr_shows_the_normalized_metadata():
    text = repr(WebFunction(add, slug="sum-two"))

    assert text.startswith("WebFunction(")
    assert "name='add'" in text
    assert "slug='sum-two'" in text


def test_a_web_function_equals_itself():
    web_function = WebFunction(add)

    assert web_function == web_function


def test_two_web_functions_over_the_same_callable_are_not_equal():
    assert WebFunction(add) != WebFunction(add)


def test_a_web_function_is_not_hashable():
    with pytest.raises(TypeError, match="unhashable type: 'dict'"):
        hash(WebFunction(add))


def test_the_title_formats_the_name():
    assert title_of(WebFunction(blur_image).html) == "Blur image"


def test_only_the_first_letter_of_the_name_is_upper_cased():
    html = WebFunction(read_HTML_pages).html

    assert title_of(html) == "Read HTML pages"
    assert heading_of(html) == "Read HTML pages"


def test_the_formatted_name_reaches_the_heading():
    assert heading_of(WebFunction(mi_informe).html) == "Mi informe"


def test_an_explicit_name_is_formatted_too():
    assert title_of(WebFunction(add, name="mi_informe").html) == "Mi informe"


def test_a_name_already_written_to_be_read_does_not_change():
    assert title_of(WebFunction(add, name="Blur image").html) == "Blur image"


@pytest.mark.parametrize("function", [blur_image, read_HTML_pages])
def test_the_name_attribute_is_not_formatted(function):
    assert WebFunction(function).name == function.__name__


def test_fn_must_be_callable():
    with pytest.raises(TypeError, match="^fn must be callable$"):
        WebFunction(42)


def test_name_must_be_str():
    with pytest.raises(TypeError, match="^name must be str$"):
        WebFunction(add, name=42)


def test_description_must_be_str():
    with pytest.raises(TypeError, match="^description must be str$"):
        WebFunction(add, description=42)


def test_slug_must_be_str():
    with pytest.raises(TypeError, match="^slug must be str$"):
        WebFunction(add, slug=42)


@pytest.mark.parametrize("value", ["yes", 1, 0])
def test_capture_prints_must_be_bool_or_none(value):
    with pytest.raises(TypeError, match="^capture_prints must be bool or None$"):
        WebFunction(add, capture_prints=value)


def test_a_callable_without_dunder_name_needs_name_and_slug():
    with pytest.raises(
        TypeError,
        match=re.escape(
            "fn must have a non-empty string __name__ when name or slug "
            "is not provided"
        ),
    ):
        WebFunction(CallableObject())


def test_a_partial_without_dunder_name_needs_name_and_slug():
    with pytest.raises(
        TypeError,
        match=re.escape(
            "fn must have a non-empty string __name__ when name or slug "
            "is not provided"
        ),
    ):
        WebFunction(partial(add, b=3))


def test_a_callable_object_is_rejected_by_the_core_even_with_metadata():
    with pytest.raises(TypeError, match="expected a plain function"):
        WebFunction(CallableObject(), name="Call", slug="call")


def test_a_partial_is_rejected_by_the_core_even_with_metadata():
    with pytest.raises(TypeError, match="expected a plain function"):
        WebFunction(partial(add, b=3), name="Partial", slug="partial")


def test_dunder_doc_must_be_str_or_none():
    def weird(a: int = 1) -> int:
        return a

    weird.__doc__ = 42

    with pytest.raises(TypeError, match="^fn.__doc__ must be str or None$"):
        WebFunction(weird)


@pytest.mark.parametrize("value", [" ", "\t", "\n"])
def test_a_name_that_strips_to_nothing_is_rejected(value):
    with pytest.raises(ValueError, match="^name cannot be empty$"):
        WebFunction(add, name=value)


@pytest.mark.parametrize("value", [" ", "   ", "\t"])
def test_a_slug_that_strips_to_nothing_is_rejected(value):
    with pytest.raises(ValueError, match="^slug cannot be empty$"):
        WebFunction(add, slug=value)


@pytest.mark.parametrize(
    "value",
    [
        "hello world",
        "hello--world",
        "a/b",
        "a\\b",
        ".",
        "..",
        "café",
        "你好",
        "-hello",
        "hello-",
        " add ",
    ],
)
def test_a_malformed_slug_is_rejected(value):
    with pytest.raises(
        ValueError,
        match=(
            "^slug must contain only letters, numbers, underscores and single "
            "hyphens$"
        ),
    ):
        WebFunction(add, slug=value)


@pytest.mark.parametrize("value", ["Hello", "hello_world", "__private__", "A1_b"])
def test_a_slug_written_as_an_identifier_is_accepted(value):
    assert WebFunction(add, slug=value).slug == value


@pytest.mark.parametrize("value", sorted(RESERVED_SLUGS))
def test_a_reserved_slug_is_rejected(value):
    with pytest.raises(ValueError, match=f"^slug '{value}' is reserved$"):
        WebFunction(add, slug=value)


def test_reserved_slugs_are_the_fixed_routes():
    assert RESERVED_SLUGS == {"doc", "static", "upload", "returns"}


@pytest.mark.parametrize("slug", ["doc", "static", "upload", "returns"])
def test_every_reserved_slug_is_refused(slug):
    with pytest.raises(ValueError, match=f"slug {slug!r} is reserved"):
        WebFunction(add, slug=slug)


def test_a_slug_that_cannot_be_derived_asks_for_an_explicit_one():
    with pytest.raises(
        ValueError,
        match=re.escape(
            "cannot derive a valid slug from fn.__name__='<lambda>'; "
            "pass slug explicitly"
        ),
    ):
        WebFunction(lambda a: a)


def test_a_lambda_is_rejected_by_the_core_even_with_an_explicit_slug():
    with pytest.raises(TypeError, match="lambdas have no usable name"):
        WebFunction(lambda a: a, name="Anonymous", slug="anonymous")


def test_a_parameter_the_core_cannot_represent_is_rejected():
    with pytest.raises(TypeError, match="unsupported type"):
        WebFunction(unsupported_parameter)


def test_a_return_that_breaks_its_contract_is_rejected():
    with pytest.raises(
        ReturnContractError,
        match="^a Download supports Path, str or bytes, not int$",
    ):
        WebFunction(broken_return)


def defaults_of(plan):
    return {field["name"]: field.get("default") for field in plan["fields"]}


def test_a_file_default_in_the_storage_compiles_to_its_reference(stored_file,
                                                                  uploads_dir):
    stored_file("a.txt")
    planted = str(uploads_dir / "a.txt")

    def read(document: TxtFile = planted) -> str:
        return document

    assert defaults_of(WebFunction(read).plan) == {"document": "a.txt"}
    assert not carries(WebFunction(read).html, uploads_dir)


def test_a_file_default_outside_the_storage_does_not_compile(sized_file):
    planted = str(sized_file("loose.txt"))

    def read(document: TxtFile = planted) -> str:
        return document

    with pytest.raises(SchemaValueError) as error:
        WebFunction(read)

    assert str(error.value) == (
        "document: default: file is not in the storage directory: 'loose.txt'")


def test_a_file_default_inside_a_dataclass_travels_as_a_reference(
        stored_file, uploads_dir):
    stored_file("a.txt")
    planted = str(uploads_dir / "a.txt")

    @dataclass
    class Box:
        document: TxtFile = planted

    def read(box: Box) -> str:
        return box.document

    node = WebFunction(read).plan["fields"][0]["node"]

    assert node["fields"][0]["default"] == "a.txt"


def test_a_list_of_file_defaults_travels_as_references(stored_file,
                                                       uploads_dir):
    stored_file("a.txt")
    stored_file("b.txt")
    planted = [str(uploads_dir / "a.txt"), str(uploads_dir / "b.txt")]

    def read(documents: list[TxtFile] = planted) -> str:
        return str(documents)

    assert defaults_of(WebFunction(read).plan) == {
        "documents": ["a.txt", "b.txt"]}


def test_a_failed_build_leaves_no_files_and_no_global_state(
    tmp_path,
    uploads_dir,
    returns_dir,
):
    import func_to_web.web.returned_files as returned_files
    import func_to_web.web.upload as upload

    def tree():
        return sorted(
            path.relative_to(tmp_path).as_posix()
            for path in tmp_path.rglob("*")
        )

    before_tree = tree()
    before_reserved = set(RESERVED_SLUGS)
    before_pattern = SLUG_PATTERN.pattern

    builders = [
        lambda: WebFunction(42),
        lambda: WebFunction(add, name=42),
        lambda: WebFunction(add, slug="hello world"),
        lambda: WebFunction(add, slug="doc"),
        lambda: WebFunction(lambda a: a),
        lambda: WebFunction(unsupported_parameter),
        lambda: WebFunction(broken_return),
        lambda: WebFunction(CallableObject()),
    ]

    for build in builders:
        with pytest.raises((TypeError, ValueError)):
            build()

    assert tree() == before_tree
    assert list(uploads_dir.iterdir()) == []
    assert list(returns_dir.iterdir()) == []
    assert RESERVED_SLUGS == before_reserved
    assert SLUG_PATTERN.pattern == before_pattern
    assert upload.UPLOADS_DIR == uploads_dir
    assert returned_files.RETURNS_DIR == returns_dir
