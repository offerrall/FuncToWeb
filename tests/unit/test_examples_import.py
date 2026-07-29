import ast
import io
import tokenize
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

COLLECTIONS = ("examples",)


def _sources():
    found = []

    for collection in COLLECTIONS:
        for path in sorted((ROOT / collection).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue

            found.append(path)

    return found


SOURCES = _sources()

IDENTIFIERS = [path.relative_to(ROOT).as_posix() for path in SOURCES]


def _called_names(node):
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Call):
            continue

        function = inner.func

        if isinstance(function, ast.Name):
            yield function.id
        elif isinstance(function, ast.Attribute):
            yield function.attr


def test_the_collections_hold_the_expected_amount_of_modules():
    assert len(SOURCES) >= 80


@pytest.mark.parametrize("source", SOURCES, ids=IDENTIFIERS)
def test_every_module_of_the_collections_compiles(source):
    compile(source.read_text(encoding="utf-8"), str(source), "exec")


@pytest.mark.parametrize("source", SOURCES, ids=IDENTIFIERS)
def test_no_module_of_the_collections_carries_a_comment(source):
    text = source.read_text(encoding="utf-8")
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    comments = [
        (token.start[0], token.string)
        for token in tokens
        if token.type == tokenize.COMMENT
    ]

    assert comments == []


@pytest.mark.parametrize("source", SOURCES, ids=IDENTIFIERS)
def test_no_module_of_the_collections_serves_anything_at_import_time(source):
    tree = ast.parse(source.read_text(encoding="utf-8"))
    guarded = [
        node for node in tree.body
        if isinstance(node, ast.If) and "__main__" in ast.unparse(node.test)
    ]
    top_level = [node for node in tree.body if node not in guarded]
    called = {name for node in top_level for name in _called_names(node)}

    assert "run" not in called
