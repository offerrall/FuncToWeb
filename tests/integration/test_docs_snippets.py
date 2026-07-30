import ast
import inspect
import json
import re
from dataclasses import MISSING, dataclass, fields
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import func_to_web
from func_to_web import (
    Choices,
    Color,
    Description,
    Download,
    IsPathFile,
    Label,
    Max,
    Min,
    OpenForm,
    Pattern,
    WebFunction,
    WebFunctions,
    page_of,
    router_of,
    run,
)

ROOT = Path(__file__).resolve().parents[2]

DOCUMENTED_PAGES = (
    "README.md",
    "docs/getting-started.md",
    "docs/run.md",
    "docs/router.md",
    "docs/web-function.md",
    "docs/open-form.md",
    "docs/outputs.md",
    "docs/files.md",
    "docs/prefill.md",
    "docs/http.md",
    "docs/streaming.md",
    "docs/types.md",
    "docs/sdk.md",
)

DELIBERATE_FRAGMENTS = {
    ("README.md", 241),
    ("docs/prefill.md", 191),
    ("docs/router.md", 7),
    ("docs/run.md", 7),
}

FENCE = re.compile(r"^```(\S*)\s*$")

STATIC_REFERENCE = re.compile(r'\.\./static/([A-Za-z0-9_./-]+)')

ImagePath = Annotated[str, IsPathFile(extensions=(".png", ".jpg", ".jpeg"))]

DISK_REPORTS: list[Path] = []
MEMORY_REPORTS: list[bytes] = []


@dataclass(frozen=True)
class Block:
    path: Path
    line: int
    language: str
    code: str

    @property
    def relative(self):
        return self.path.relative_to(ROOT).as_posix()

    @property
    def location(self):
        return (self.relative, self.line)

    @property
    def label(self):
        return f"{self.relative}:{self.line}"


def fenced_blocks(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    found = []
    index = 0

    while index < len(lines):
        opening = FENCE.match(lines[index])

        if opening is None:
            index += 1
            continue

        start = index + 1
        end = start

        while end < len(lines) and lines[end].strip() != "```":
            end += 1

        found.append(Block(path, start + 1, opening.group(1),
                           "\n".join(lines[start:end])))
        index = end + 1

    return found


def markdown_pages():
    return sorted(ROOT.glob("docs/**/*.md")) + [ROOT / "README.md"]


def python_blocks():
    return [block
            for path in markdown_pages()
            for block in fenced_blocks(path)
            if block.language == "python"]


def blocks_of(language):
    return [block
            for path in markdown_pages()
            for block in fenced_blocks(path)
            if block.language == language]


def signature_block(page, name):
    for block in fenced_blocks(ROOT / page):
        if block.language == "python" and block.code.startswith(f"{name}(\n"):
            return block

    raise AssertionError(f"no {name}() signature block in {page}")


def documented_parameters(code):
    function = ast.parse(f"def {code}:\n    pass\n").body[0]
    arguments = function.args
    listed = [(item.arg, "positional")
              for item in arguments.posonlyargs + arguments.args]

    return listed + [(item.arg, "keyword") for item in arguments.kwonlyargs]


def documented_defaults(code):
    function = ast.parse(f"def {code}:\n    pass\n").body[0]
    arguments = function.args
    plain = arguments.posonlyargs + arguments.args
    written = {}

    for item, default in zip(plain[len(plain) - len(arguments.defaults):],
                             arguments.defaults):
        written[item.arg] = ast.unparse(default)

    for item, default in zip(arguments.kwonlyargs, arguments.kw_defaults):
        if default is not None:
            written[item.arg] = ast.unparse(default)

    return written


def real_parameters(target):
    return [
        (parameter.name,
         "keyword" if parameter.kind is parameter.KEYWORD_ONLY
         else "positional")
        for parameter in inspect.signature(target).parameters.values()
    ]


def real_defaults(target):
    return {
        parameter.name: repr(parameter.default)
        for parameter in inspect.signature(target).parameters.values()
        if parameter.default is not parameter.empty
    }


def imported_from_func_to_web(code):
    names = []

    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.ImportFrom) and node.module == "func_to_web":
            names.extend(alias.name for alias in node.names)

    return names


def lower_layer_imports(code):
    modules = []

    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)

    return [module for module in modules
            if module.startswith(("pytypehint", "func_to_web."))]


ALL_PYTHON_BLOCKS = python_blocks()

FRAGMENT_BLOCKS = [block for block in ALL_PYTHON_BLOCKS
                   if block.location in DELIBERATE_FRAGMENTS]

COMPLETE_BLOCKS = [block for block in ALL_PYTHON_BLOCKS
                   if block.location not in DELIBERATE_FRAGMENTS]

IMPORTING_BLOCKS = [block for block in COMPLETE_BLOCKS
                    if "func_to_web" in block.code]


def ids_of(blocks):
    return [block.label for block in blocks]


def divide(a: float, b: float) -> float:
    return a / b


def add(a: int, b: int) -> int:
    """Suma dos números."""
    return a + b


def volume(
    width: Annotated[int, Min(1), Max(100)],
    height: Annotated[int, Min(1), Max(100)],
    depth: int = 10,
) -> float:
    """Multiplica tres dimensiones."""
    return width * height * depth


@dataclass
class Order:
    product: str
    quantity: Annotated[int, Min(1), Max(100)]


def create_order(order: Order) -> str:
    return f"{order.quantity} × {order.product}"


@dataclass
class Product:
    product_id: int
    name: str
    stock: int


PRODUCTS = {7: Product(7, "Chair", 12)}


def edit_product(product_id: int, name: str, stock: int) -> str:
    PRODUCTS[product_id] = Product(product_id, name, stock)

    return "Product updated"


def select_product(
    product_id: int,
) -> Annotated[Product, OpenForm(edit_product, hidden=("product_id",))]:
    return PRODUCTS[product_id]


def report() -> Annotated[Path, Download()]:
    return DISK_REPORTS[0]


def report_in_memory() -> Annotated[bytes, Download(filename="report.pdf")]:
    return MEMORY_REPORTS[0]


def process() -> tuple[
    str,
    Annotated[list[Path], Download()],
    Annotated[list[bytes], Download(
        filename=lambda _value, index: f"memory-{index + 1}.pdf"
    )],
]:
    return "Finished", list(DISK_REPORTS), list(MEMORY_REPORTS)


def blur(image: ImagePath, radius: int = 8) -> str:
    return f"{Path(image).name}:{radius}"


def montage(images: Annotated[list[ImagePath], Min(1), Max(3)]) -> str:
    return str(len(images))


def edit_user(
    name: str = "",
    age: Annotated[int, Min(0), Max(120)] = 0,
) -> str:
    return f"{name}:{age}"


def percentage(value: Annotated[int, Min(0), Max(100)]) -> int:
    return value


def average(
    values: Annotated[
        list[Annotated[int, Min(0), Max(100)]],
        Min(1),
        Max(20),
    ],
) -> float:
    return sum(values) / len(values)


@dataclass
class Limits:
    minimum: int
    maximum: int


def configure(limits: Limits) -> str:
    return f"{limits.minimum} - {limits.maximum}"


def set_color(color: Color) -> str:
    return color


def normal_task(times: int = 2) -> str:
    for index in range(times):
        print(f"normal-{index}")

    return "normal"


def noisy_task(times: int = 2) -> str:
    for index in range(times):
        print(f"noisy-{index}")

    return "noisy"


def create_tag(name: str) -> str:
    return f"tag {name}"


@pytest.fixture
def clients():
    made = []

    def make(app, **options):
        client = TestClient(app, **options)
        made.append(client)

        return client

    yield make

    for client in made:
        client.close()


@pytest.fixture(autouse=True)
def clear_download_sources():
    DISK_REPORTS.clear()
    MEMORY_REPORTS.clear()
    yield
    DISK_REPORTS.clear()
    MEMORY_REPORTS.clear()


def test_the_documentation_pages_the_snippets_come_from_exist(repo_root):
    assert ROOT == repo_root

    for page in DOCUMENTED_PAGES:
        assert (ROOT / page).is_file()


def test_the_documentation_really_carries_python_snippets():
    covered = {block.relative for block in ALL_PYTHON_BLOCKS}

    assert len(ALL_PYTHON_BLOCKS) > 30
    assert set(DOCUMENTED_PAGES) <= covered


@pytest.mark.parametrize("block", COMPLETE_BLOCKS, ids=ids_of(COMPLETE_BLOCKS))
def test_every_complete_python_block_parses(block):
    ast.parse(block.code)


@pytest.mark.parametrize("block", FRAGMENT_BLOCKS, ids=ids_of(FRAGMENT_BLOCKS))
def test_every_declared_fragment_really_is_a_fragment(block):
    with pytest.raises(SyntaxError):
        ast.parse(block.code)


def test_the_fragment_list_names_exactly_the_blocks_that_do_not_parse():
    broken = set()

    for block in ALL_PYTHON_BLOCKS:
        try:
            ast.parse(block.code)
        except SyntaxError:
            broken.add(block.location)

    assert broken == DELIBERATE_FRAGMENTS


@pytest.mark.parametrize("block", IMPORTING_BLOCKS, ids=ids_of(IMPORTING_BLOCKS))
def test_every_name_imported_from_func_to_web_is_public(block):
    imported = imported_from_func_to_web(block.code)

    assert set(imported) <= set(func_to_web.__all__)

    for name in imported:
        assert hasattr(func_to_web, name)


@pytest.mark.parametrize("block", COMPLETE_BLOCKS, ids=ids_of(COMPLETE_BLOCKS))
def test_no_snippet_imports_from_a_lower_layer(block):
    assert lower_layer_imports(block.code) == []


def test_the_documentation_imports_cover_a_real_part_of_the_public_api():
    imported = {name
                for block in IMPORTING_BLOCKS
                for name in imported_from_func_to_web(block.code)}

    assert {"run", "router_of", "page_of", "WebFunction", "WebFunctions",
            "OpenForm", "Download"} <= imported


@pytest.mark.parametrize(
    ("page", "name", "target"),
    [
        ("docs/run.md", "run", run),
        ("docs/router.md", "router_of", router_of),
        ("docs/prefill.md", "page_of", page_of),
        ("docs/web-function.md", "WebFunction", WebFunction),
    ],
)
def test_the_documented_signature_matches_the_real_one(page, name, target):
    block = signature_block(page, name)

    assert documented_parameters(block.code) == real_parameters(target)
    assert documented_defaults(block.code) == real_defaults(target)


def test_the_documented_open_form_dataclass_matches_the_real_one():
    block = next(item for item in fenced_blocks(ROOT / "docs/open-form.md")
                 if item.language == "python"
                 and item.code.startswith("@dataclass(frozen=True)"))
    declared = ast.parse(block.code).body[0]
    written = [(node.target.id,
                None if node.value is None else ast.unparse(node.value))
               for node in declared.body]
    real = [(item.name,
             None if item.default is MISSING else repr(item.default))
            for item in fields(OpenForm)]

    assert declared.name == "OpenForm"
    assert [name for name, _ in written] == [name for name, _ in real]
    assert written == [("target", None), ("hidden", "()")]
    assert real == [("target", None), ("hidden", "()")]


def test_the_readme_first_example_runs(client_factory):
    client = client_factory(divide)

    assert inspect.signature(run).bind(divide)
    assert client.get("/divide/").status_code == 200
    assert client.post("/divide/invoke", json={"a": 6, "b": 3}).json() == {
        "result": {"type": "text", "value": "2.0"}
    }
    assert client.get("/doc").status_code == 200
    assert "divide" in client.get("/doc").text


def test_the_readme_first_example_reports_a_failure_as_an_error(client_factory):
    client = client_factory(divide)
    answer = client.post("/divide/invoke", json={"a": 1, "b": 0})

    assert answer.status_code == 500
    assert answer.json()["error"].startswith("ZeroDivisionError:")


def test_the_getting_started_form_derives_its_bounds_from_the_signature(
    client_factory, plan_of_page
):
    client = client_factory(volume)
    plan = plan_of_page(client.get("/volume/").text)
    named = {field["name"]: field for field in plan["fields"]}

    assert named["width"]["node"]["options"]["min"] == 1
    assert named["width"]["node"]["options"]["max"] == 100
    assert named["height"]["node"]["options"]["min"] == 1
    assert named["height"]["node"]["options"]["max"] == 100
    assert named["depth"]["hasDefault"] is True
    assert named["depth"]["default"] == 10
    assert plan["description"] == "Multiplica tres dimensiones."


def test_the_getting_started_routes_are_the_documented_ones(client_factory):
    client = client_factory(volume)

    assert client.get("/volume/").status_code == 200
    assert client.post("/volume/invoke", json={"width": 3, "height": 4}).status_code == 200
    assert client.get("/doc").status_code == 200


def test_the_getting_started_curl_answer_is_still_true(client_factory):
    documented = json.loads(
        next(block.code
             for block in fenced_blocks(ROOT / "docs/getting-started.md")
             if block.language == "json")
    )
    client = client_factory(volume)

    assert client.post("/volume/invoke",
                       json={"width": 3, "height": 4}).json() == documented


def test_the_readme_fastapi_integration_snippet_works(clients):
    app = FastAPI()
    app.include_router(router_of([add, divide]), prefix="/tools")
    client = clients(app)
    page = client.get("/tools/add/").text
    asset = STATIC_REFERENCE.search(page).group(1)

    assert client.get("/tools/add/").status_code == 200
    assert client.get("/tools/divide/").status_code == 200
    assert client.post("/tools/add/invoke", json={"a": 1, "b": 2}).json() == {
        "result": {"type": "text", "value": "3"}
    }
    assert client.post("/tools/divide/invoke", json={"a": 6, "b": 3}).status_code == 200
    assert client.get("/tools/doc").status_code == 200
    assert client.get(f"/tools/static/{asset}").status_code == 200
    assert client.get("/add/").status_code == 404


def test_the_readme_dataclass_snippet_reaches_the_function(client_factory):
    client = client_factory(create_order)

    assert client.post("/create_order/invoke",
                       json={"order": {"product": "Chair", "quantity": 2}}
                       ).json() == {
        "result": {"type": "text", "value": "2 × Chair"}
    }
    assert client.post("/create_order/invoke",
                       json={"order": {"product": "Chair", "quantity": 0}}
                       ).status_code == 422


def test_the_readme_reexport_snippet_imports_real_objects():
    assert (Choices, Description, Label, Max, Min, Pattern) == (
        func_to_web.Choices,
        func_to_web.Description,
        func_to_web.Label,
        func_to_web.Max,
        func_to_web.Min,
        func_to_web.Pattern,
    )


def test_the_web_function_metadata_snippet_still_applies():
    prepared = WebFunction(divide, name="Dividir", slug="division")

    assert prepared.name == "Dividir"
    assert prepared.slug == "division"
    assert WebFunction(add).slug == "add"
    assert WebFunction(add).description == "Suma dos números."


def test_the_web_function_named_space_is_reachable(clients):
    app = FastAPI()
    app.include_router(router_of(
        [volume, WebFunction(divide, name="Dividir", slug="division")],
        title="Herramientas internas",
    ))
    client = clients(app)

    assert client.get("/division/").status_code == 200
    assert client.post("/division/invoke", json={"a": 6, "b": 3}).status_code == 200
    assert client.get("/doc").text.startswith("=== Herramientas internas ===")
    assert client.get("/divide/").status_code == 404


def test_the_web_functions_snippet_builds_a_prepared_space(clients):
    space = WebFunctions(
        (
            WebFunction(add),
            WebFunction(divide, name="Dividir", slug="division"),
        ),
        title="Herramientas internas",
    )
    app = FastAPI()
    app.include_router(router_of(space), prefix="/a")
    app.include_router(router_of(space), prefix="/b")
    client = clients(app)

    assert space.title == "Herramientas internas"
    assert [item.slug for item in space.functions] == ["add", "division"]
    assert client.post("/a/add/invoke", json={"a": 1, "b": 2}).status_code == 200
    assert client.post("/b/division/invoke", json={"a": 6, "b": 3}).status_code == 200

    with pytest.raises(TypeError,
                       match="the prepared space already carries its title"):
        router_of(space, title="Otro")


def test_the_open_form_snippet_opens_the_target_prefilled(clients):
    app = FastAPI()
    app.include_router(router_of([select_product, edit_product]),
                       prefix="/tools")
    client = clients(app)
    result = client.post("/tools/select_product/invoke",
                         json={"product_id": 7}).json()["result"]
    query = parse_qs(urlparse(result["href"]).query)

    assert result["type"] == "form"
    assert result["href"].startswith("../edit_product/?")
    assert json.loads(query["prefill"][0]) == {
        "product_id": 7,
        "name": "Chair",
        "stock": 12,
    }
    assert json.loads(query["hidden"][0]) == ["product_id"]
    assert client.get("/tools/edit_product/",
                      params={"prefill": query["prefill"][0],
                              "hidden": query["hidden"][0]}).status_code == 200


def test_the_open_form_target_must_be_registered():
    from func_to_web import ReturnContractError

    with pytest.raises(ReturnContractError,
                       match="OpenForm target is not registered in this space"):
        router_of([select_product])

    with pytest.raises(ReturnContractError,
                       match="matches more than one registered function"):
        router_of([
            WebFunction(edit_product, slug="edit-a"),
            WebFunction(edit_product, slug="edit-b"),
            select_product,
        ])


def test_the_download_snippet_offers_a_stored_path(client_factory, tmp_path):
    source = tmp_path / "report.pdf"
    source.write_bytes(b"%PDF-1.4 disk")
    DISK_REPORTS.append(source)
    client = client_factory(report)
    result = client.post("/report/invoke", json={}).json()["result"]

    assert result["type"] == "download"
    assert result["filename"] == "report.pdf"
    assert client.get(f"/returns/{result['value']}").content == b"%PDF-1.4 disk"
    assert source.read_bytes() == b"%PDF-1.4 disk"


def test_the_download_snippet_offers_bytes_built_in_memory(client_factory):
    MEMORY_REPORTS.append(b"%PDF-1.4 memory")
    client = client_factory(report_in_memory)
    result = client.post("/report_in_memory/invoke", json={}).json()["result"]

    assert result["type"] == "download"
    assert result["filename"] == "report.pdf"
    assert client.get(f"/returns/{result['value']}").content == b"%PDF-1.4 memory"


def test_the_multiple_download_snippet_keeps_the_return_order(
    client_factory, tmp_path
):
    source = tmp_path / "disk.pdf"
    source.write_bytes(b"disk")
    DISK_REPORTS.append(source)
    MEMORY_REPORTS.extend([b"one", b"two"])
    client = client_factory(process)
    outputs = client.post("/process/invoke", json={}).json()["result"]

    assert [item["type"] for item in outputs] == [
        "text", "download", "download", "download",
    ]
    assert outputs[0]["value"] == "Finished"
    assert [item["filename"] for item in outputs[1:]] == [
        "disk.pdf", "memory-1.pdf", "memory-2.pdf",
    ]


def test_the_theme_snippet_writes_the_documented_html_root(clients, html_root):
    app = FastAPI()
    app.include_router(router_of([add, divide]), prefix="/system")
    app.include_router(router_of([add, divide], theme="light"), prefix="/light")
    app.include_router(router_of([add, divide], theme="dark"), prefix="/dark")
    client = clients(app)

    assert html_root(client.get("/system/add/").text) == "<html>"
    assert html_root(client.get("/light/add/").text) == (
        '<html data-pth-theme="light">'
    )
    assert html_root(client.get("/dark/add/").text) == (
        '<html data-pth-theme="dark">'
    )


def test_the_theme_snippet_errors_are_the_documented_ones():
    with pytest.raises(ValueError,
                       match=r"theme must be one of system, light, dark; "
                             r"got 'Dark'"):
        router_of([add, divide], theme="Dark")

    with pytest.raises(TypeError, match="theme must be str"):
        router_of([add, divide], theme=None)


def test_the_file_field_snippet_uploads_once_and_invokes_many_times(
    client_factory, uploads_dir, stored_bytes
):
    client = client_factory([blur, montage], max_upload_bytes=50 * 1024 * 1024)
    uploaded = client.post("/upload", content=b"PNGDATA",
                           headers={"X-File-Reference": "photo-1234.png"})

    assert uploaded.status_code == 200
    assert uploaded.json() == {"uploaded": True}
    assert stored_bytes("photo-1234.png") == b"PNGDATA"
    assert client.post("/blur/invoke",
                       json={"image": "photo-1234.png", "radius": 8}).json() == {
        "result": {"type": "text", "value": "photo-1234.png:8"}
    }
    assert client.post("/blur/invoke",
                       json={"image": "photo-1234.png", "radius": 2}).json() == {
        "result": {"type": "text", "value": "photo-1234.png:2"}
    }


def test_the_file_field_snippet_rejects_a_reference_that_is_a_path(
    client_factory
):
    client = client_factory([blur, montage])
    separators = client.post("/upload", content=b"x",
                             headers={"X-File-Reference": "../evil.pdf"})
    bare = client.post("/upload", content=b"x",
                       headers={"X-File-Reference": ".."})

    assert separators.status_code == 400
    assert separators.json()["detail"].endswith("cannot contain separators")
    assert bare.status_code == 400
    assert bare.json()["detail"].endswith("must be a file name")


def test_the_multiple_file_snippet_applies_the_list_bounds(
    client_factory, uploads_dir
):
    client = client_factory([blur, montage])
    names = ["a.png", "b.png", "c.png", "d.png"]

    for name in names:
        client.post("/upload", content=b"PNG",
                    headers={"X-File-Reference": name})

    assert client.post("/montage/invoke", json={"images": names[:3]}).json() == {
        "result": {"type": "text", "value": "3"}
    }
    assert client.post("/montage/invoke",
                       json={"images": names}).json()["error"].endswith(
        "images: too many items: 4, maximum 3"
    )


def test_the_prefill_snippet_produces_a_page_with_values(client_factory):
    web_function = WebFunction(edit_user)
    html = page_of(web_function, prefill={"name": "Ana", "age": 32})

    assert "Ana" in html
    assert html != web_function.html
    assert page_of(web_function) == web_function.html

    with pytest.raises(ValueError, match="unknown prefill field: 'nope'"):
        page_of(web_function, prefill={"nope": 1})

    with pytest.raises(TypeError,
                       match="hidden must be an iterable of str, "
                             "not a single str"):
        page_of(web_function, hidden="name")


def test_the_prefill_query_answers_the_documented_codes(client_factory,
                                                        plan_of_page):
    client = client_factory(edit_user)
    good = client.get("/edit_user/",
                      params={"prefill": json.dumps({"name": "Ana",
                                                     "age": 32})})
    plan = plan_of_page(good.text)
    named = {field["name"]: field for field in plan["fields"]}

    assert good.status_code == 200
    assert named["name"]["default"] == "Ana"
    assert named["age"]["default"] == 32
    assert client.get("/edit_user/",
                      params={"prefill": "{not json"}).status_code == 400
    assert client.get("/edit_user/",
                      params={"prefill": "[1, 2]"}).json()["detail"] == (
        "prefill must be a JSON object"
    )
    assert client.get("/edit_user/",
                      params={"prefill": '{"nope": 1}'}).json()["detail"] == (
        "unknown prefill field: 'nope'"
    )
    assert client.get("/edit_user/",
                      params={"hidden": '{"a":1}'}).json()["detail"] == (
        "hidden must be a JSON array"
    )
    assert client.get("/edit_user/",
                      params={"hidden": '["a",1]'}).json()["detail"] == (
        "hidden must contain only strings"
    )


def test_the_http_snippet_reads_the_documented_envelope(client_factory):
    client = client_factory(create_tag)
    payload = client.post("/create_tag/invoke", json={"name": "demo"}).json()

    assert "error" not in payload
    assert payload["result"] == {"type": "text", "value": "tag demo"}


def test_the_http_snippet_status_codes_are_the_documented_ones(client_factory):
    client = client_factory([create_tag, divide])
    missing = client.post("/create_tag/invoke", json={})
    extra = client.post("/create_tag/invoke", json={"name": "x", "zzz": 1})
    crashing = client.post("/divide/invoke", json={"a": 1, "b": 0})

    assert missing.status_code == 422
    assert missing.json() == {
        "error": "SchemaTypeError: missing argument(s): name"
    }
    assert extra.status_code == 422
    assert extra.json() == {
        "error": "SchemaTypeError: unexpected argument(s): zzz"
    }
    assert crashing.status_code == 500
    assert set(crashing.json()) == {"error"}


def test_the_streaming_snippet_switches_capture_per_function(clients, sse):
    app = FastAPI()
    app.include_router(router_of(
        [
            normal_task,
            WebFunction(noisy_task, capture_prints=False),
        ],
        capture_prints=True,
    ))
    client = clients(app)
    quiet = sse(client.post("/noisy_task/invoke-stream", json={}).text)
    loud = sse(client.post("/normal_task/invoke-stream", json={}).text)

    assert [name for name, _ in quiet] == ["start", "result"]
    assert [name for name, _ in loud][0] == "start"
    assert "print" in [name for name, _ in loud]
    assert "".join(payload["text"]
                   for name, payload in loud if name == "print") == (
        "normal-0\nnormal-1\n"
    )


def test_the_types_snippets_validate_before_calling(client_factory):
    client = client_factory([percentage, average, configure, set_color])

    assert client.post("/percentage/invoke", json={"value": 50}).json() == {
        "result": {"type": "text", "value": "50"}
    }
    assert client.post("/percentage/invoke", json={"value": 101}).status_code == 422
    assert client.post("/percentage/invoke", json={"value": "50"}).status_code == 422
    assert client.post("/average/invoke",
                       json={"values": [10, 20]}).json() == {
        "result": {"type": "text", "value": "15.0"}
    }
    assert client.post("/average/invoke", json={"values": []}).status_code == 422
    assert client.post("/configure/invoke",
                       json={"limits": {"minimum": 1, "maximum": 9}}).json() == {
        "result": {"type": "text", "value": "1 - 9"}
    }
    assert client.post("/set_color/invoke",
                       json={"color": "#ff0000"}).json() == {
        "result": {"type": "text", "value": "#ff0000"}
    }
    assert client.post("/set_color/invoke",
                       json={"color": "red"}).status_code == 422


def test_the_run_reserved_kwargs_raise_the_documented_errors():
    with pytest.raises(TypeError,
                       match="fastapi_kwargs cannot contain 'title'; "
                             "use the title argument"):
        run(divide, fastapi_kwargs={"title": "Otro"})

    with pytest.raises(TypeError,
                       match="uvicorn_kwargs cannot contain 'host'; "
                             "use the host argument"):
        run(divide, uvicorn_kwargs={"host": "0.0.0.0"})

    with pytest.raises(TypeError,
                       match="uvicorn_kwargs cannot contain 'app'; "
                             "run\\(\\) builds it internally"):
        run(divide, uvicorn_kwargs={"app": object()})


def test_the_router_error_table_of_the_documentation_holds():
    with pytest.raises(ValueError,
                       match="at least one function is required"):
        router_of([])

    for entry in (None, 3, "add", {"a": add}):
        with pytest.raises(TypeError,
                           match="entries must be callables or WebFunction "
                                 "instances"):
            router_of(entry)

    with pytest.raises(TypeError,
                       match="entries must be callables or WebFunction "
                             "instances"):
        router_of([add, 3])

    with pytest.raises(ValueError,
                       match="two functions share the slug 'add'"):
        router_of([add, WebFunction(divide, slug="add")])


def test_the_documented_reserved_slugs_are_still_reserved():
    for reserved in ("doc", "static"):
        with pytest.raises(ValueError, match=f"slug '{reserved}' is reserved"):
            WebFunction(add, slug=reserved)


def test_the_documented_slug_derivation_still_holds():
    def save_result() -> str:
        return ""

    def load__cache() -> str:
        return ""

    def MyFunction() -> str:
        return ""

    assert WebFunction(save_result).slug == "save_result"
    assert WebFunction(load__cache).slug == "load__cache"
    assert WebFunction(MyFunction).slug == "MyFunction"

    with pytest.raises(ValueError,
                       match="cannot derive a valid slug from "
                             "fn.__name__='<lambda>'"):
        WebFunction(lambda: "")


def test_the_documented_download_union_rules_still_hold():
    from func_to_web import ReturnContractError

    def allowed_pair(a: int = 1) -> Annotated[Path | str, Download()]:
        return Path("x")

    def allowed_optional(a: int = 1) -> Annotated[Path, Download()] | None:
        return None

    def forbidden(a: int = 1) -> Annotated[Path, Download()] | str:
        return "x"

    assert WebFunction(allowed_pair).return_parser is not None
    assert WebFunction(allowed_optional).return_parser is not None

    with pytest.raises(ReturnContractError,
                       match="a union cannot mix Download and ordinary return "
                             "branches"):
        WebFunction(forbidden)


def test_the_documented_open_form_limits_still_hold():
    from func_to_web import ReturnContractError

    def twice(a: int = 1) -> tuple[
        Annotated[dict, OpenForm(edit_product)],
        Annotated[dict, OpenForm(edit_product)],
    ]:
        return {}, {}

    with pytest.raises(ReturnContractError,
                       match="OpenForm can only mark the whole return, and "
                             "only once"):
        WebFunction(twice)

    with pytest.raises(TypeError, match="OpenForm.hidden must be a tuple"):
        OpenForm(edit_product, hidden=["product_id"])


def test_the_documented_open_form_return_contract_still_holds(client_factory):
    def picks_wrong(a: int = 1) -> Annotated[Any, OpenForm(create_tag)]:
        return "not a mapping"

    client = client_factory([picks_wrong, create_tag])
    answer = client.post("/picks_wrong/invoke", json={})

    assert answer.status_code == 500
    assert answer.json() == {
        "error": "ReturnContractError: OpenForm return must be a mapping or "
                 "dataclass instance"
    }
