"""What 2.6.0 retired, and the boundary it must not cross back over.

pytypehint 1.0.0 renamed IsPathFile to FileHint with no alias, and stopped
checking existence, is_file() and byte size during Signature.build(). Two
things can quietly undo that: the old name creeping back into code or prose,
and prose that keeps crediting the core with a guarantee it no longer makes.
The same release moved the pin to pytypehintweb 1.1.0, whose decode() delegates
the portable reading to the core and keeps only the walk that hands file nodes
to the host's resolver.

The point is not to police vocabulary. Each pattern below stands for one
retired promise, and the allowances are the documents whose job is to describe
a past release faithfully. The checks that follow them stand for the shape of
the dependency: FuncToWeb reads pytypehintweb's public API and nothing else,
and it never reads the transport itself.
"""

import ast
import re
import tomllib

import pytest

SCANNED_TREES = (
    ("src", ("*.py", "*.js", "*.css", "*.html")),
    ("docs", ("*.md",)),
    ("examples", ("*.py", "*.md")),
)

SCANNED_FILES = ("README.md", "CHANGELOG.md", "pyproject.toml")

# Documents that describe releases where these names and messages were true.
# Rewriting them would falsify history, so they are named one by one rather
# than waved through by a directory rule.
HISTORICAL = (
    "CHANGELOG.md",
    "docs/design/history-1.6-to-2.0.md",
    "docs/migration-1.6-to-2.0.md",
)

# (label, pattern, allowed paths)
RETIRED = (
    (
        "the pre-2.6.0 name of FileHint",
        re.compile(r"\bIsPathFile\b"),
        HISTORICAL,
    ),
    (
        "a build()-time size verdict the core no longer produces",
        re.compile(r"file too small", re.IGNORECASE),
        HISTORICAL,
    ),
    (
        "a build()-time size verdict the core no longer produces",
        re.compile(r"file too large", re.IGNORECASE),
        HISTORICAL,
    ),
    (
        # Only an exact pin of a version this release moved past. A bare
        # `pytypehintweb`, a link to it or a prose mention is the normal way
        # to name the dependency and stays untouched; what must not reappear
        # is a superseded pin presented as what 2.6.0 installs.
        "a pytypehintweb pin 2.6.0 moved past",
        re.compile(r"pytypehintweb\s*==\s*(?:0\.0\.5|1\.0\.0)\b"),
        HISTORICAL,
    ),
)

# The adapter FuncToWeb reads the transport through. Which of its names are
# public is asked of its own __all__ rather than copied here, so the check
# stays true the day the adapter publishes something new.
PACKAGE = "pytypehintweb"

# FileHint's byte bounds belong to the browser. FuncToWeb must not grow a
# second reader of them: a resolver that stats the file to enforce min_size or
# max_size would be exactly the duplicated schema validator this release
# refuses. Prose is free to mention them, so this one is scoped to the package.
SIZE_BOUND = re.compile(r"\b(min_size|max_size)\b")

# A runtime dependency names one version and one only: `name==1.2.3`, with an
# optional extras bracket. Anything with a range in it fails this.
PIN = re.compile(r"[A-Za-z0-9._-]+(\[[A-Za-z0-9,._-]+\])?==[A-Za-z0-9.]+")

# mypy settings that would hand back what removing untyped_calls_exclude won.
EXEMPTIONS = frozenset({
    "untyped_calls_exclude",
    "disable_error_code",
    "ignore_errors",
    "follow_imports",
    "ignore_missing_imports",
    "allow_untyped_calls",
})


def relative(path, repo_root):
    return path.relative_to(repo_root).as_posix()


def scanned(repo_root):
    for directory, patterns in SCANNED_TREES:
        root = repo_root / directory

        if not root.is_dir():
            continue

        for pattern in patterns:
            for path in sorted(root.rglob(pattern)):
                if "__pycache__" in path.parts:
                    continue

                yield path

    for name in SCANNED_FILES:
        path = repo_root / name

        if path.is_file():
            yield path


def hits(pattern, path):
    text = path.read_text(encoding="utf-8", errors="replace")

    return [number for number, line in enumerate(text.splitlines(), 1)
            if pattern.search(line)]


def modules(repo_root):
    """Every module of the package, parsed.

    The two checks below read syntax, not text: a regexp over import lines
    misreads a parenthesised import and accuses a comment that merely names
    the adapter, and neither mistake is one a reviewer should have to argue
    with.
    """
    for path in sorted((repo_root / "src").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue

        text = path.read_text(encoding="utf-8")

        yield path, ast.parse(text, filename=str(path))


def adapter_imports(tree):
    """(node, module, imported names) for every import naming the adapter."""
    for node in ast.walk(tree):
        if type(node) is ast.Import:
            for alias in node.names:
                if alias.name == PACKAGE or alias.name.startswith(
                        f"{PACKAGE}."):
                    yield node, alias.name, ()

        elif type(node) is ast.ImportFrom:
            module = node.module or ""

            if module == PACKAGE or module.startswith(f"{PACKAGE}."):
                yield node, module, tuple(alias.name for alias in node.names)


def literal(node):
    return type(node) is ast.Constant and type(node.value) is str


def codec_names(tree):
    """Module-level names bound to a string, which a codec may travel under.

    `raw.decode(ASCII)` is still a bytes decode, and reading the constant is
    what keeps the check below from calling it a schema read; a schema never
    arrives as a module-level string, so nothing is waved through by this.
    """
    names = set()

    for node in tree.body:
        if type(node) is ast.Assign and literal(node.value):
            names.update(target.id for target in node.targets
                         if type(target) is ast.Name)
        elif (type(node) is ast.AnnAssign and node.value is not None
                and literal(node.value) and type(node.target) is ast.Name):
            names.add(node.target.id)

    return names


def names_a_codec(node, codecs):
    return literal(node) or (type(node) is ast.Name and node.id in codecs)


@pytest.mark.parametrize(("label", "pattern", "allowed"), RETIRED,
                         ids=[pattern.pattern for _, pattern, _ in RETIRED])
def test_a_retired_promise_appears_nowhere_outside_its_history(
    label, pattern, allowed, repo_root
):
    found = []

    for path in scanned(repo_root):
        name = relative(path, repo_root)

        if name in allowed:
            continue

        found += [f"{name}:{number}" for number in hits(pattern, path)]

    assert found == [], f"{label} survives in: {', '.join(found)}"


@pytest.mark.parametrize("name", HISTORICAL)
def test_every_allowed_historical_document_still_exists(name, repo_root):
    # An allowance for a file that is gone is an allowance nobody reviews.
    assert (repo_root / name).is_file()


def test_the_package_never_reads_the_file_size_bounds(repo_root):
    found = []

    for path in sorted((repo_root / "src").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue

        found += [f"{relative(path, repo_root)}:{number}"
                  for number in hits(SIZE_BOUND, path)]

    assert found == [], (
        "FileHint byte bounds are the browser's; the package must not read "
        f"them: {', '.join(found)}")


def test_the_package_imports_only_the_public_api_of_the_adapter(repo_root):
    """`from pytypehintweb import <names of __all__>`, and nothing else.

    A submodule import reaches past what the adapter promises: pytypehintweb
    1.1.0 rewrote the whole of decode.py without touching a single name of
    __all__, and a package that had reached inside it would have had to be
    rewritten with it. A private name is the same bet with no promise at all.
    """
    import pytypehintweb

    public = set(pytypehintweb.__all__)
    seen = []
    refused = []

    for path, tree in modules(repo_root):
        for node, module, names in adapter_imports(tree):
            where = f"{relative(path, repo_root)}:{node.lineno}"
            seen.append(where)

            if module != PACKAGE:
                refused.append(f"{where} imports the submodule {module}")
            elif not names:
                refused.append(f"{where} imports the whole package")
            else:
                refused += [f"{where} imports {name!r}, which is not in "
                            f"{PACKAGE}.__all__"
                            for name in names if name not in public]

    # Without this the check would pass on a package that had stopped using
    # the adapter, or on a scan that had stopped finding anything.
    assert seen, f"no import of {PACKAGE} found in src/"
    assert refused == [], "; ".join(refused)


def test_the_package_never_decodes_a_schema_itself(repo_root):
    """schema.decode() is the core's half; FuncToWeb calls decode() instead.

    pytypehintweb.decode() runs schema.decode() and then walks the result
    handing every file node to the resolver. Calling the core directly skips
    that walk, so the package would have to grow its own FileHint traversal —
    the duplicated walker this design refuses — and the references would reach
    the function unresolved.

    A bytes decoding is told apart by what it is handed: it names its codec,
    and its error policy if it has one, inline. A schema decoding is handed
    data, so anything with an argument that is not a string literal is one.
    """
    refused = []

    for path, tree in modules(repo_root):
        codecs = codec_names(tree)

        for node in ast.walk(tree):
            if type(node) is not ast.Call:
                continue

            if type(node.func) is not ast.Attribute:
                continue

            if node.func.attr != "decode":
                continue

            if (all(names_a_codec(argument, codecs) for argument in node.args)
                    and all(names_a_codec(word.value, codecs)
                            for word in node.keywords)):
                continue

            refused.append(f"{relative(path, repo_root)}:{node.lineno}")

    assert refused == [], (
        "the transport is read once, by pytypehintweb.decode(); the package "
        f"must not decode a schema itself: {', '.join(refused)}")


def project(repo_root):
    with (repo_root / "pyproject.toml").open("rb") as file:
        return tomllib.load(file)


def test_every_runtime_dependency_is_pinned_to_one_version(repo_root):
    # The operator, not just the number. A range would let an install pick a
    # pytypehintweb this release was never run against, and the version test
    # in test_package.py compares the built metadata against the same
    # pyproject: relaxing both at once would agree with itself.
    loose = [requirement
             for requirement in project(repo_root)["project"]["dependencies"]
             if PIN.fullmatch(requirement) is None]

    assert loose == [], (
        "runtime dependencies are pinned to an exact version: "
        f"{', '.join(loose)}")


def test_the_type_checker_keeps_no_exemption_for_the_adapter(repo_root):
    # 1.1.0 annotates decode(), which is what let 2.6.0 drop
    # untyped_calls_exclude. Nothing else runs mypy in this suite, so without
    # this the exemption could come back green.
    mypy = project(repo_root)["tool"]["mypy"]

    assert mypy.get("strict") is True, "mypy must stay strict"

    relaxed = sorted(key for key in mypy if key in EXEMPTIONS)

    assert relaxed == [], (
        "the adapter is fully annotated as of pytypehintweb 1.1.0, so the "
        f"package type checks with no exemption: {', '.join(relaxed)}")
    assert "overrides" not in mypy, (
        "a per-module override is an exemption by another name")
