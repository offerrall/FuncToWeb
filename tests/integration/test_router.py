from typing import Annotated

import pytest
from starlette.routing import Route

from func_to_web import (
    Download,
    FileHint,
    OpenForm,
    WebFunction,
    WebFunctions,
    app_of,
)

TxtFile = Annotated[str, FileHint(extensions=(".txt",))]

DOC_ROUTE = ("/doc", ("GET",))
STATIC_ROUTE = ("/static/{name:path}", ("GET",))
INDEX_ROUTE = ("/", ("GET",))
UPLOAD_ROUTE = ("/upload", ("POST",))
RETURNS_ROUTE = ("/returns/{reference}", ("GET",))


def routes_of(app):
    return [(route.path, tuple(sorted(route.methods - {"HEAD"})))
            for route in app.routes if isinstance(route, Route)]


def paths_of(app):
    return [path for path, _ in routes_of(app)]


def group_of(slug):
    return [
        (f"/{slug}/", ("GET",)),
        (f"/{slug}/invoke", ("POST",)),
        (f"/{slug}/invoke-stream", ("POST",)),
    ]


def takes_file(document: TxtFile) -> str:
    """Takes a file."""
    return document


def makes_file(seed: int = 1) -> Annotated[bytes, Download("out.txt")]:
    """Makes a file."""
    return b"x" * seed


def numbered(value, index):
    return f"file-{index}.bin"


def makes_files(seed: int = 2) -> Annotated[list[bytes], Download(numbered)]:
    """Makes several files."""
    return [b"x"] * seed


def takes_optional_file(document: TxtFile | None = None) -> str:
    """Takes an optional file."""
    return str(document)


def multiply(a: int, b: int = 3) -> int:
    """Multiply two numbers."""
    return a * b


def edit_product(product_id: int, name: str = "x") -> str:
    """Edits a product."""
    return name


def select_product(product_id: int = 1) -> Annotated[
    dict,
    OpenForm(edit_product, hidden=("product_id",)),
]:
    """Selects a product."""
    return {"product_id": product_id, "name": "chosen"}


def doc(a: int = 1) -> int:
    """Derives the reserved doc slug."""
    return a


def static(a: int = 1) -> int:
    """Derives the reserved static slug."""
    return a


def MyTool(a: int = 1) -> int:
    """Keeps its capitals in the slug."""
    return a


def test_a_single_function_registers_only_the_five_fixed_routes(
    app_factory, scalar,
):
    app = app_factory(scalar)

    assert routes_of(app) == [*group_of("add"), DOC_ROUTE, STATIC_ROUTE,
                              INDEX_ROUTE]


def test_each_function_registers_its_own_group_in_space_order(
    app_factory, scalar,
):
    app = app_factory([scalar, multiply])

    assert routes_of(app) == [
        *group_of("add"),
        *group_of("multiply"),
        DOC_ROUTE,
        STATIC_ROUTE,
        INDEX_ROUTE,
    ]


def test_invoke_rejects_get(client_factory, scalar):
    client = client_factory(scalar)

    assert client.get("/add/invoke").status_code == 405


def test_invoke_stream_rejects_get(client_factory, scalar):
    client = client_factory(scalar)

    assert client.get("/add/invoke-stream").status_code == 405


def test_page_rejects_post(client_factory, scalar):
    client = client_factory(scalar)

    assert client.post("/add/").status_code == 405


def test_doc_rejects_post(client_factory, scalar):
    client = client_factory(scalar)

    assert client.post("/doc").status_code == 405


def test_upload_is_registered_when_a_function_takes_a_file(
    app_factory, file_function,
):
    app = app_factory(file_function)

    assert UPLOAD_ROUTE in routes_of(app)


def test_upload_is_absent_without_file_fields(app_factory, scalar):
    app = app_factory(scalar)

    assert UPLOAD_ROUTE not in routes_of(app)
    assert "/upload" not in paths_of(app)


def test_upload_is_registered_for_a_file_nested_in_a_dataclass_list(
    app_factory, nested_function,
):
    app = app_factory(nested_function)

    assert UPLOAD_ROUTE in routes_of(app)


def test_upload_is_registered_for_an_optional_file_field(app_factory):
    app = app_factory(takes_optional_file)

    assert UPLOAD_ROUTE in routes_of(app)


def test_upload_answers_only_when_registered(client_factory, scalar):
    client = client_factory(scalar)

    response = client.post("/upload", content=b"x",
                           headers={"X-File-Reference": "a.txt"})

    assert response.status_code == 404


def test_returns_is_registered_when_a_function_declares_download(
    app_factory,
):
    app = app_factory(makes_file)

    assert RETURNS_ROUTE in routes_of(app)


def test_returns_is_absent_without_download(app_factory, scalar):
    app = app_factory(scalar)

    assert RETURNS_ROUTE not in routes_of(app)
    assert not any(path.startswith("/returns") for path in paths_of(app))


def test_returns_is_registered_for_a_list_of_downloads(app_factory):
    app = app_factory(makes_files)

    assert RETURNS_ROUTE in routes_of(app)


def test_returns_answers_only_when_registered(client_factory, scalar):
    client = client_factory(scalar)

    assert client.get("/returns/anything").status_code == 404


def test_one_function_with_a_download_registers_returns_for_the_whole_space(
    app_factory, scalar,
):
    app = app_factory([scalar, makes_file])

    assert RETURNS_ROUTE in routes_of(app)


def test_registration_order_is_functions_upload_returns_doc_static(
    app_factory,
):
    app = app_factory([takes_file, makes_file])

    assert routes_of(app) == [
        *group_of("takes_file"),
        *group_of("makes_file"),
        UPLOAD_ROUTE,
        RETURNS_ROUTE,
        DOC_ROUTE,
        STATIC_ROUTE,
        INDEX_ROUTE,
    ]


def test_no_route_is_registered_twice(app_factory, scalar):
    app = app_factory([scalar, multiply, takes_file, makes_file,
                       select_product, edit_product])

    registered = routes_of(app)

    assert len(registered) == len(set(registered))
    assert len(registered) == 6 * 3 + 5


def test_no_path_carries_two_registrations_of_the_same_method(
    app_factory, scalar,
):
    app = app_factory([scalar, takes_file, makes_file])

    pairs = [(path, method)
             for path, methods in routes_of(app)
             for method in methods]

    assert len(pairs) == len(set(pairs))


def test_title_does_not_change_the_route_graph(app_factory, scalar):
    plain = app_factory(scalar)
    titled = app_factory(scalar, title="Internal tools")

    assert routes_of(titled) == routes_of(plain)


def test_title_reaches_the_document(client_factory, scalar):
    client = client_factory(scalar, title="Internal tools")

    assert "Internal tools" in client.get("/doc").text


def test_default_title_is_func_to_web(client_factory, scalar):
    client = client_factory(scalar)

    assert "FuncToWeb" in client.get("/doc").text


def test_theme_does_not_change_the_route_graph(app_factory, scalar):
    plain = app_factory(scalar)
    dark = app_factory(scalar, theme="dark")

    assert routes_of(dark) == routes_of(plain)


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_theme_reaches_every_page_of_the_space(
    client_factory, scalar, html_root, theme,
):
    client = client_factory([scalar, multiply], theme=theme)

    for slug in ("add", "multiply"):
        html = client.get(f"/{slug}/").text

        assert html_root(html) == f'<html data-pth-theme="{theme}">'


def test_system_theme_leaves_the_html_tag_bare(client_factory, scalar,
                                               html_root):
    client = client_factory(scalar)

    assert html_root(client.get("/add/").text) == "<html>"


@pytest.mark.parametrize("theme", ["Dark", "auto", "light "])
def test_an_unknown_theme_is_refused_when_the_router_is_built(scalar, theme):
    with pytest.raises(ValueError, match="theme must be one of"):
        app_of(scalar, theme=theme)


def test_a_non_string_theme_is_refused_when_the_router_is_built(scalar):
    with pytest.raises(TypeError, match="theme must be str"):
        app_of(scalar, theme=None)


def test_capture_prints_does_not_change_the_route_graph(
    app_factory, printing,
):
    enabled = app_factory(printing, capture_prints=True)
    disabled = app_factory(printing, capture_prints=False)

    assert routes_of(disabled) == routes_of(enabled)


def test_capture_prints_true_streams_the_printed_lines(
    client_factory, printing, sse,
):
    client = client_factory(printing, capture_prints=True)

    response = client.post("/chatty/invoke-stream", json={"times": 2})
    names = [name for name, _ in sse(response.text)]

    assert "print" in names


def test_capture_prints_false_streams_no_printed_lines(
    client_factory, printing, sse,
):
    client = client_factory(printing, capture_prints=False)

    response = client.post("/chatty/invoke-stream", json={"times": 2})
    names = [name for name, _ in sse(response.text)]

    assert names == ["start", "result"]


def test_a_web_function_overrides_the_space_capture_prints(
    client_factory, printing, sse,
):
    client = client_factory(WebFunction(printing, capture_prints=True),
                            capture_prints=False)

    response = client.post("/chatty/invoke-stream", json={"times": 2})
    names = [name for name, _ in sse(response.text)]

    assert "print" in names


def test_max_upload_bytes_does_not_change_the_route_graph(
    app_factory, file_function,
):
    plain = app_factory(file_function)
    limited = app_factory(file_function, max_upload_bytes=16)

    assert routes_of(limited) == routes_of(plain)


def test_max_upload_bytes_limits_the_upload_route(
    client_factory, file_function,
):
    client = client_factory(file_function, max_upload_bytes=4)

    response = client.post("/upload", content=b"x" * 40,
                           headers={"X-File-Reference": "a.txt"})

    assert response.status_code == 413


def test_without_max_upload_bytes_the_upload_route_imposes_no_limit(
    client_factory, file_function,
):
    client = client_factory(file_function)

    response = client.post("/upload", content=b"x" * 4096,
                           headers={"X-File-Reference": "a.txt"})

    assert response.status_code == 200


def test_max_upload_bytes_is_validated_when_the_router_is_built(scalar):
    with pytest.raises(ValueError, match="greater than zero"):
        app_of(scalar, max_upload_bytes=0)


def test_a_non_integer_max_upload_bytes_is_refused(scalar):
    with pytest.raises(TypeError, match="max_upload_bytes must be int"):
        app_of(scalar, max_upload_bytes="4")


def test_the_doc_slug_is_reserved():
    with pytest.raises(ValueError, match="'doc' is reserved"):
        app_of(doc)


def test_the_static_slug_is_reserved():
    with pytest.raises(ValueError, match="'static' is reserved"):
        app_of(static)


def test_an_explicit_reserved_slug_is_refused(scalar):
    with pytest.raises(ValueError, match="'doc' is reserved"):
        app_of(WebFunction(scalar, slug="doc"))


@pytest.mark.parametrize("slug", ["upload", "returns"])
def test_a_slug_that_names_a_fixed_route_is_refused(slug):
    with pytest.raises(ValueError, match=f"slug {slug!r} is reserved"):
        WebFunction(takes_file, slug=slug)


@pytest.mark.parametrize("slug", ["upload", "returns"])
def test_a_reserved_slug_is_refused_even_without_that_route(scalar, slug):
    with pytest.raises(ValueError, match="is reserved"):
        WebFunction(scalar, slug=slug)


def test_a_name_with_capitals_registers_the_route_with_them(app_factory):
    app = app_factory(MyTool)

    assert routes_of(app) == [*group_of("MyTool"), DOC_ROUTE, STATIC_ROUTE,
                              INDEX_ROUTE]


def test_the_route_of_a_slug_is_case_sensitive(client_factory):
    client = client_factory(MyTool)

    assert client.get("/MyTool/").status_code == 200
    assert client.get("/mytool/").status_code == 404


def test_invoke_is_case_sensitive_too(client_factory):
    client = client_factory(MyTool)

    assert client.post("/MyTool/invoke", json={"a": 1}).status_code == 200
    assert client.post("/mytool/invoke", json={"a": 1}).status_code == 404


def test_open_form_registers_no_extra_route(app_factory):
    app = app_factory([select_product, edit_product])

    assert routes_of(app) == [
        *group_of("select_product"),
        *group_of("edit_product"),
        DOC_ROUTE,
        STATIC_ROUTE,
        INDEX_ROUTE,
    ]


def test_open_form_between_functions_of_the_same_space_resolves(
    client_factory,
):
    client = client_factory([select_product, edit_product])

    result = client.post("/select_product/invoke",
                         json={"product_id": 7}).json()["result"]

    assert result["type"] == "form"
    assert result["href"].startswith("../edit_product/?")


def test_open_form_alone_in_the_space_is_refused():
    with pytest.raises(TypeError, match="not registered in this space"):
        app_of(select_product)


def test_open_form_does_not_register_the_returns_route(app_factory):
    app = app_factory([select_product, edit_product])

    assert RETURNS_ROUTE not in routes_of(app)


def test_the_same_prepared_space_serves_from_two_routers(
    client_factory, scalar,
):
    space = WebFunctions((WebFunction(scalar),), title="Shared")

    first = client_factory(space, prefix="/one")
    second = client_factory(space, prefix="/two")

    assert first.post("/one/add/invoke", json={"a": 1, "b": 2}).json() == {
        "result": {"type": "text", "value": "3"}
    }
    assert second.post("/two/add/invoke", json={"a": 1, "b": 2}).json() == {
        "result": {"type": "text", "value": "3"}
    }


def test_mounting_a_prepared_space_twice_does_not_alter_it(scalar):
    space = WebFunctions((WebFunction(scalar),), title="Shared")
    before = (space.functions, space.title, space.document, dict(space.forms))

    app_of(space)
    app_of(space, theme="dark")

    assert space.functions is before[0]
    assert space.title == before[1]
    assert space.document == before[2]
    assert space.forms == before[3]


def test_two_routers_over_one_space_keep_their_own_theme(
    client_factory, scalar, html_root,
):
    space = WebFunctions((WebFunction(scalar),), title="Shared")

    light = client_factory(space, prefix="/light", theme="light")
    dark = client_factory(space, prefix="/dark", theme="dark")

    assert html_root(light.get("/light/add/").text) == (
        '<html data-pth-theme="light">'
    )
    assert html_root(dark.get("/dark/add/").text) == (
        '<html data-pth-theme="dark">'
    )


def test_the_compiled_html_of_a_shared_space_is_never_rewritten(scalar):
    web_function = WebFunction(scalar)
    space = WebFunctions((web_function,), title="Shared")
    compiled = web_function.html

    app_of(space, theme="dark")

    assert web_function.html == compiled


def test_a_prepared_space_refuses_a_second_title(scalar):
    space = WebFunctions((WebFunction(scalar),), title="Shared")

    with pytest.raises(TypeError, match="already carries its title"):
        app_of(space, title="Other")
