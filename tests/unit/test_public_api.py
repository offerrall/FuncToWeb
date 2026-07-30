import ast
import inspect
import json
import os
import subprocess
import sys
from dataclasses import is_dataclass

import pytest

import func_to_web
import pytypehint
import pytypehintweb
from func_to_web.models.function import WebFunction as _WebFunction
from func_to_web.models.function import page_of as _page_of
from func_to_web.models.functions import WebFunctions as _WebFunctions
from func_to_web.models.return_parser import Download as _Download
from func_to_web.models.return_parser import OpenForm as _OpenForm
from func_to_web.models.return_parser import (
    ReturnContractError as _ReturnContractError,
)
from func_to_web.templates.theme import Theme as _Theme
from func_to_web.web.router import router_of as _router_of
from func_to_web.web.run import run as _run

OWN_NAMES = (
    "run",
    "router_of",
    "page_of",
    "WebFunction",
    "WebFunctions",
    "Download",
    "OpenForm",
    "ReturnContractError",
    "Theme",
    "__version__",
)

INTERNAL_NAMES = (
    "ReturnParser",
    "FormAction",
    "has_download",
    "parser_of",
    "space_of",
    "has_file",
)

PYTYPEHINT_NAMES = (
    "Min",
    "Max",
    "Choices",
    "MultipleOf",
    "Pattern",
    "IsPathFile",
    "Label",
    "Description",
    "Placeholder",
    "Step",
    "Slider",
    "IsPassword",
    "Rows",
    "Extra",
    "OptionalToggle",
    "SchemaTypeError",
    "SchemaValueError",
)

PYTYPEHINTWEB_NAMES = (
    "Color",
    "Email",
    "COLOR_PATTERN",
    "EMAIL_PATTERN",
)

DOCUMENTED_SIGNATURES = (
    ("run", "run.md"),
    ("router_of", "router.md"),
    ("page_of", "prefill.md"),
)

DOCSTRING_OWNERS = (
    "run",
    "router_of",
    "page_of",
    "WebFunction",
    "WebFunctions",
    "Download",
    "OpenForm",
    "ReturnContractError",
)

PROBE = r'''
import json
import os
import pathlib
import sys
import tempfile
import threading

made = []
path_mkdir = pathlib.Path.mkdir
os_mkdir = os.mkdir
os_makedirs = os.makedirs


def spy_path_mkdir(self, *args, **kwargs):
    made.append(str(self))
    return path_mkdir(self, *args, **kwargs)


def spy_os_mkdir(path, *args, **kwargs):
    made.append(str(path))
    return os_mkdir(path, *args, **kwargs)


def spy_os_makedirs(name, *args, **kwargs):
    made.append(str(name))
    return os_makedirs(name, *args, **kwargs)


pathlib.Path.mkdir = spy_path_mkdir
os.mkdir = spy_os_mkdir
os.makedirs = spy_os_makedirs

from platformdirs import user_data_path

uploads = user_data_path("FuncToWeb", appauthor=False) / "uploads"
returns = pathlib.Path(tempfile.gettempdir()) / "FuncToWeb" / "returns"

threads_before = threading.active_count()
stdout_before = sys.stdout

import func_to_web

pathlib.Path.mkdir = path_mkdir
os.mkdir = os_mkdir
os.makedirs = os_makedirs

print("PROBE" + json.dumps({
    "made": made,
    "uploads_exists": uploads.exists(),
    "returns_exists": returns.exists(),
    "uploads_path": str(uploads),
    "returns_path": str(returns),
    "threads_before": threads_before,
    "threads_after": threading.active_count(),
    "stdout_unchanged": sys.stdout is stdout_before,
    "stdout_is_original": sys.stdout is sys.__stdout__,
    "stdout_type": type(sys.stdout).__name__,
    "uvicorn_imported": "uvicorn" in sys.modules,
    "excepthook_is_original": sys.excepthook is sys.__excepthook__,
}))
'''


def _clean_import(tmp_path, repo_root):
    home = tmp_path / "home"
    home.mkdir()

    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(repo_root / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    for variable in ("LOCALAPPDATA", "APPDATA", "XDG_DATA_HOME", "HOME",
                     "USERPROFILE", "TMP", "TEMP", "TMPDIR"):
        environment[variable] = str(home)

    completed = subprocess.run(
        [sys.executable, "-c", PROBE],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr

    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    marked = [line for line in lines if line.startswith("PROBE")]

    assert len(marked) == 1, completed.stdout

    return json.loads(marked[0][len("PROBE"):]), lines


@pytest.mark.parametrize("name", func_to_web.__all__)
def test_every_name_listed_in_all_is_reachable_on_the_package(name):
    assert hasattr(func_to_web, name)


def test_all_lists_no_name_twice():
    assert len(func_to_web.__all__) == len(set(func_to_web.__all__))


def test_all_exports_no_private_name():
    private = [name for name in func_to_web.__all__
               if name.startswith("_") and not name.startswith("__")]

    assert private == []


def test_all_is_exactly_the_own_names_plus_the_documented_reexports():
    expected = set(OWN_NAMES) | set(PYTYPEHINT_NAMES) | set(PYTYPEHINTWEB_NAMES)

    assert set(func_to_web.__all__) == expected


def test_version_is_the_published_two_zero_zero():
    assert func_to_web.__version__ == "2.1.0"


def test_theme_is_exported_and_is_the_theme_of_the_templates_module():
    assert func_to_web.Theme is _Theme


@pytest.mark.parametrize("name", ("run", "router_of", "page_of"))
def test_the_three_entry_points_are_callable(name):
    assert callable(getattr(func_to_web, name))


@pytest.mark.parametrize(
    ("name", "expected"),
    (
        ("run", _run),
        ("router_of", _router_of),
        ("page_of", _page_of),
        ("WebFunction", _WebFunction),
        ("WebFunctions", _WebFunctions),
        ("Download", _Download),
        ("OpenForm", _OpenForm),
        ("ReturnContractError", _ReturnContractError),
    ),
)
def test_own_public_names_are_the_objects_their_modules_define(name, expected):
    assert getattr(func_to_web, name) is expected


@pytest.mark.parametrize("name", INTERNAL_NAMES)
def test_the_resolution_machinery_is_not_reexported(name):
    assert name not in func_to_web.__all__
    assert not hasattr(func_to_web, name)


@pytest.mark.parametrize(
    "name",
    ("WebFunction", "WebFunctions", "Download", "OpenForm"),
)
def test_public_model_classes_are_frozen_dataclasses(name):
    cls = getattr(func_to_web, name)

    assert isinstance(cls, type)
    assert is_dataclass(cls)
    assert cls.__dataclass_params__.frozen is True


def test_return_contract_error_is_a_type_error_subclass():
    assert isinstance(func_to_web.ReturnContractError, type)
    assert issubclass(func_to_web.ReturnContractError, TypeError)


@pytest.mark.parametrize("name", PYTYPEHINT_NAMES)
def test_pytypehint_reexports_are_the_very_objects_of_pytypehint(name):
    assert getattr(func_to_web, name) is getattr(pytypehint, name)


@pytest.mark.parametrize("name", PYTYPEHINTWEB_NAMES)
def test_pytypehintweb_reexports_are_the_very_objects_of_pytypehintweb(name):
    assert getattr(func_to_web, name) is getattr(pytypehintweb, name)


def test_importing_the_package_creates_no_directory(tmp_path, repo_root):
    probe, _ = _clean_import(tmp_path, repo_root)

    assert probe["made"] == []


def test_importing_the_package_leaves_the_storage_directories_absent(
    tmp_path,
    repo_root,
):
    probe, _ = _clean_import(tmp_path, repo_root)

    assert probe["uploads_exists"] is False
    assert probe["returns_exists"] is False


def test_importing_the_package_does_not_wrap_stdout_for_print_capture(
    tmp_path,
    repo_root,
):
    probe, _ = _clean_import(tmp_path, repo_root)

    assert probe["stdout_unchanged"] is True
    assert probe["stdout_is_original"] is True
    assert probe["stdout_type"] == "TextIOWrapper"


def test_importing_the_package_starts_no_server_and_prints_nothing(
    tmp_path,
    repo_root,
):
    probe, lines = _clean_import(tmp_path, repo_root)

    assert probe["uvicorn_imported"] is False
    assert probe["threads_after"] == probe["threads_before"] == 1
    assert probe["excepthook_is_original"] is True
    assert len(lines) == 1


@pytest.mark.parametrize(("name", "document"), DOCUMENTED_SIGNATURES)
def test_public_signature_matches_the_one_written_in_the_docs(
    name,
    document,
    repo_root,
):
    text = (repo_root / "docs" / document).read_text(encoding="utf-8")
    opening = f"```python\n{name}("
    start = text.index(opening) + len("```python\n")
    end = text.index("```", start)
    tree = ast.parse("def " + text[start:end].strip() + ": ...").body[0]
    arguments = tree.args

    documented = []
    padding = len(arguments.args) - len(arguments.defaults)

    for index, argument in enumerate(arguments.args):
        documented.append((
            argument.arg,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.empty if index < padding
            else ast.literal_eval(arguments.defaults[index - padding]),
        ))

    for argument, node in zip(arguments.kwonlyargs, arguments.kw_defaults):
        documented.append((
            argument.arg,
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.empty if node is None
            else ast.literal_eval(node),
        ))

    actual = [
        (parameter.name, parameter.kind, parameter.default)
        for parameter in inspect.signature(
            getattr(func_to_web, name)).parameters.values()
    ]

    assert actual == documented
    assert arguments.vararg is None
    assert arguments.kwarg is None
    assert arguments.posonlyargs == []


@pytest.mark.parametrize("name", DOCSTRING_OWNERS)
def test_public_objects_carry_a_non_empty_docstring(name):
    docstring = getattr(func_to_web, name).__doc__

    assert type(docstring) is str
    assert docstring.strip() != ""


def test_theme_is_documented_where_it_is_declared(repo_root):
    source = (repo_root / "src" / "func_to_web" / "templates" / "theme.py")
    tree = ast.parse(source.read_text(encoding="utf-8"))
    body = tree.body
    index = next(
        position for position, node in enumerate(body)
        if isinstance(node, ast.Assign)
        and node.targets[0].id == "Theme"
    )
    following = body[index + 1]

    assert isinstance(following, ast.Expr)
    assert isinstance(following.value, ast.Constant)
    assert following.value.value.strip() != ""
