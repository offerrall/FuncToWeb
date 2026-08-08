import json
import re
import subprocess
import sys
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

import pytest

pytestmark = [pytest.mark.package, pytest.mark.slow]

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src" / "func_to_web"
VERSION = "2.2.0"
WHEEL_NAME = f"func_to_web-{VERSION}-py3-none-any.whl"
SDIST_NAME = f"func_to_web-{VERSION}.tar.gz"
SDIST_PREFIX = f"func_to_web-{VERSION}/"
DIST_INFO = f"func_to_web-{VERSION}.dist-info"

FORBIDDEN_PARTS = (
    "__pycache__",
    "tests",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".git",
    ".venv",
    "venv",
    "scratchpad",
    "examples",
    "projects",
    "docs",
)

FORBIDDEN_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".whl",
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".log",
    ".sqlite",
)

FORBIDDEN_FILES = (
    ".env",
    ".env.local",
    "secrets.json",
    "credentials.json",
    "id_rsa",
)

EXPECTED_CLASSIFIERS = (
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
)

EXPECTED_RUNTIME_REQUIREMENTS = (
    "pytypehint==0.0.7",
    "pytypehintweb==0.0.5",
    "fastapi==0.121.1",
    "uvicorn==0.38.0",
)

EXPECTED_ASSETS = frozenset({
    "py.typed",
    "static/page.js",
    "static/output.js",
    "static/upload.js",
    "static/emit.js",
    "static/sdk.js",
    "static/page.css",
    "static/icons/alert.svg",
    "static/icons/check.svg",
    "static/icons/clock.svg",
    "static/icons/copy.svg",
    "static/icons/download.svg",
    "templates/page.html",
    "templates/index.html",
})

OWN_CRAWLED_ASSETS = frozenset({
    "/static/page.js",
    "/static/output.js",
    "/static/upload.js",
    "/static/page.css",
    "/static/icons/alert.svg",
    "/static/icons/check.svg",
    "/static/icons/clock.svg",
    "/static/icons/copy.svg",
    "/static/icons/download.svg",
})

_INSTALLED_PYTHON: list[Path] = []


def run(command, **extra):
    return subprocess.run(
        [str(item) for item in command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        **extra,
    )


def run_or_fail(command, label, **extra):
    result = run(command, **extra)

    if result.returncode != 0:
        pytest.fail(f"{label} failed ({result.returncode})\n"
                    f"{result.stdout}\n{result.stderr}")

    return result


def wheel_entries(wheel):
    with zipfile.ZipFile(wheel) as archive:
        return sorted(archive.namelist())


def wheel_text(wheel, name):
    with zipfile.ZipFile(wheel) as archive:
        return archive.read(name).decode("utf-8")


def normalized(text):
    return text.replace("\r\n", "\n").strip()


def sdist_entries(sdist):
    with tarfile.open(sdist) as archive:
        members = [member.name for member in archive.getmembers()
                   if member.isfile()]

    return sorted(name[len(SDIST_PREFIX):] for name in members
                  if name.startswith(SDIST_PREFIX))


def metadata_of(wheel):
    return Parser().parsestr(wheel_text(wheel, f"{DIST_INFO}/METADATA"))


def assets_on_disk():
    found = {"py.typed"}

    for path in (PACKAGE / "static").rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            found.add(path.relative_to(PACKAGE).as_posix())

    for path in (PACKAGE / "templates").rglob("*.html"):
        found.add(path.relative_to(PACKAGE).as_posix())

    return found


def assets_in(entries, prefix):
    return {name[len(prefix):] for name in entries
            if name.startswith(prefix) and not name.endswith(".py")}


def offending(entries, skip_prefixes=()):
    problems = []

    for name in entries:
        if any(name.startswith(prefix) for prefix in skip_prefixes):
            continue

        parts = Path(name).parts

        if any(part in FORBIDDEN_PARTS for part in parts[:-1]):
            problems.append(name)
        elif name.endswith(FORBIDDEN_SUFFIXES) or name.endswith(".tar.gz"):
            problems.append(name)
        elif parts[-1] in FORBIDDEN_FILES:
            problems.append(name)

    return problems


def venv_python(home):
    for candidate in (home / "Scripts" / "python.exe", home / "bin" / "python"):
        if candidate.is_file():
            return candidate

    raise RuntimeError(f"no interpreter inside {home}")


def payload_of(result):
    lines = [line for line in result.stdout.splitlines() if line.strip()]

    if not lines:
        pytest.fail(f"subprocess produced no output\n{result.stderr}")

    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        pytest.fail(f"unexpected output\n{result.stdout}\n{result.stderr}")


def run_in_venv(interpreter, source, workdir, name="probe.py"):
    script = workdir / name
    script.write_text(source, encoding="utf-8")
    result = run([interpreter, script], cwd=str(workdir))

    if result.returncode != 0:
        pytest.fail(f"{name} failed in the installed venv "
                    f"({result.returncode})\n{result.stdout}\n{result.stderr}")

    return payload_of(result)


DEMO_SOURCE = '''
def demo(name: str = "x", count: int = 1) -> str:
    """Demo function."""
    return name * count
'''

IMPORT_PROBE = '''
import json

import func_to_web

namespace = {}
exec("from func_to_web import *", namespace)

print(json.dumps({
    "file": func_to_web.__file__,
    "version": func_to_web.__version__,
    "exported": sorted(func_to_web.__all__),
    "missing_attribute": sorted(name for name in func_to_web.__all__
                                if not hasattr(func_to_web, name)),
    "missing_star": sorted(name for name in func_to_web.__all__
                           if name not in namespace),
}))
'''

ROUTER_PROBE = DEMO_SOURCE + '''
import json

from fastapi import APIRouter, FastAPI
from func_to_web import router_of

router = router_of(demo)

app = FastAPI()
app.include_router(router)

print(json.dumps({
    "type": type(router).__name__,
    "is_api_router": isinstance(router, APIRouter),
    "routes": sorted(route.path for route in router.routes),
}))
'''

PAGE_PROBE = DEMO_SOURCE + '''
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from func_to_web import router_of

app = FastAPI()
app.include_router(router_of(demo))

with TestClient(app) as client:
    page = client.get("/demo/")
    doc = client.get("/doc")

print(json.dumps({
    "page_status": page.status_code,
    "page_has_root": 'class="pth-root"' in page.text,
    "doc_status": doc.status_code,
    "doc_text": doc.text,
}))
'''

CRAWL_PROBE = DEMO_SOURCE + '''
import json
import re
from urllib.parse import urljoin

from fastapi import FastAPI
from fastapi.testclient import TestClient
from func_to_web import router_of

HTML_REFERENCE = re.compile(r'(?:href|src)="([^"]+)"')
SCRIPT_REFERENCE = re.compile(r'(?:from|import)\\s*\\(?\\s*"([^"]+)"')
STYLE_REFERENCE = re.compile(r'url\\(\\s*["\\\']?([^"\\\')]+)["\\\']?\\s*\\)')

app = FastAPI()
app.include_router(router_of(demo))

seen = {}
pending = ["/demo/"]

with TestClient(app) as client:
    while pending:
        url = pending.pop()

        if url in seen:
            continue

        response = client.get(url)
        seen[url] = response.status_code

        if response.status_code != 200:
            continue

        if url.endswith(".css"):
            references = STYLE_REFERENCE.findall(response.text)
        elif url.endswith(".js"):
            references = SCRIPT_REFERENCE.findall(response.text)
        elif url.endswith((".svg", ".png", ".ico")):
            references = []
        else:
            references = HTML_REFERENCE.findall(response.text)

        for reference in references:
            if reference.startswith(("http:", "https:", "data:", "#", "//")):
                continue

            pending.append(urljoin(url, reference))

print(json.dumps({"resources": seen}))
'''


@pytest.fixture(scope="module")
def distribution(tmp_path_factory):
    outdir = tmp_path_factory.mktemp("package_dist")
    result = run([sys.executable, "-m", "build", "--outdir", outdir, ROOT])

    if result.returncode != 0:
        pytest.fail(f"python -m build failed ({result.returncode})\n"
                    f"{result.stdout}\n{result.stderr}")

    return {
        "outdir": outdir,
        "wheels": sorted(outdir.glob("*.whl")),
        "sdists": sorted(outdir.glob("*.tar.gz")),
    }


@pytest.fixture(scope="module")
def wheel(distribution):
    return distribution["wheels"][0]


@pytest.fixture(scope="module")
def sdist(distribution):
    return distribution["sdists"][0]


@pytest.fixture
def installed_python(distribution, local_pytypehintweb, tmp_path_factory):
    if _INSTALLED_PYTHON:
        return _INSTALLED_PYTHON[0]

    home = tmp_path_factory.mktemp("package_venv")
    run_or_fail([sys.executable, "-m", "venv", home], "python -m venv")

    interpreter = venv_python(home)
    install = [interpreter, "-m", "pip", "install", "--disable-pip-version-check"]

    run_or_fail(install + [local_pytypehintweb], "pip install pytypehintweb")
    run_or_fail(install + [distribution["wheels"][0], "httpx"],
                "pip install func-to-web wheel")

    _INSTALLED_PYTHON.append(interpreter)

    return interpreter


def test_build_produces_one_wheel_and_one_sdist(distribution):
    assert [path.name for path in distribution["wheels"]] == [WHEEL_NAME]
    assert [path.name for path in distribution["sdists"]] == [SDIST_NAME]
    assert distribution["wheels"][0].stat().st_size > 0
    assert distribution["sdists"][0].stat().st_size > 0


def test_twine_check_approves_both_artifacts(wheel, sdist):
    result = run([sys.executable, "-m", "twine", "check", wheel, sdist])

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count("PASSED") == 2, result.stdout
    assert "WARNING" not in result.stdout


def test_wheel_metadata_declares_name_and_version(wheel):
    metadata = metadata_of(wheel)

    assert metadata["Name"] == "func-to-web"
    assert metadata["Version"] == VERSION


def test_wheel_version_matches_the_source_of_truth(wheel):
    from func_to_web import __version__

    config = (PACKAGE / "config.py").read_text(encoding="utf-8")
    declared = re.search(r'^__version__ = "([^"]+)"', config, re.MULTILINE)

    assert declared is not None
    assert declared.group(1) == VERSION
    assert __version__ == VERSION
    assert metadata_of(wheel)["Version"] == VERSION


def test_wheel_metadata_pins_runtime_dependencies(wheel):
    metadata = metadata_of(wheel)
    runtime = [value for value in metadata.get_all("Requires-Dist", [])
               if "extra ==" not in value]

    assert runtime == list(EXPECTED_RUNTIME_REQUIREMENTS)


def test_wheel_metadata_requires_supported_python(wheel):
    assert metadata_of(wheel)["Requires-Python"] == ">=3.11"


def test_wheel_metadata_lists_every_classifier(wheel):
    classifiers = metadata_of(wheel).get_all("Classifier", [])

    assert classifiers == list(EXPECTED_CLASSIFIERS)


def test_wheel_metadata_embeds_the_readme(wheel):
    metadata = metadata_of(wheel)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    body = metadata.get_payload()

    assert metadata["Description-Content-Type"] == "text/markdown"
    assert normalized(body) == normalized(readme)


def test_wheel_metadata_and_archive_carry_the_license(wheel):
    metadata = metadata_of(wheel)
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

    assert "MIT License" in metadata["License"]
    assert "LICENSE" in metadata.get_all("License-File", [])

    packaged = wheel_text(wheel, f"{DIST_INFO}/licenses/LICENSE")

    assert normalized(packaged) == normalized(license_text)


def test_wheel_ships_every_expected_asset(wheel):
    entries = set(wheel_entries(wheel))

    for asset in sorted(EXPECTED_ASSETS):
        assert f"func_to_web/{asset}" in entries


def test_wheel_assets_match_the_source_tree(wheel):
    packaged = assets_in(wheel_entries(wheel), "func_to_web/")
    on_disk = assets_on_disk()

    assert packaged == on_disk, (
        f"missing from the wheel: {sorted(on_disk - packaged)}; "
        f"unexpected in the wheel: {sorted(packaged - on_disk)}"
    )


def test_wheel_ships_the_five_icons(wheel):
    icons = [name for name in wheel_entries(wheel)
             if name.startswith("func_to_web/static/icons/")]

    assert len(icons) == 5
    assert all(name.endswith(".svg") for name in icons)


def test_wheel_has_no_bytecode_or_development_leftovers(wheel):
    entries = wheel_entries(wheel)

    assert offending(entries, skip_prefixes=(DIST_INFO + "/",)) == []
    assert not any("__pycache__" in name for name in entries)


def test_wheel_excludes_the_test_suite(wheel):
    entries = wheel_entries(wheel)

    assert not any(name.startswith("tests/") for name in entries)
    assert not any("/tests/" in name for name in entries)
    assert not any(name.startswith("func_to_web/tests") for name in entries)


def test_wheel_only_holds_the_package_and_its_metadata(wheel):
    unexpected = [name for name in wheel_entries(wheel)
                  if not name.startswith(("func_to_web/", DIST_INFO + "/"))]

    assert unexpected == []


def test_sdist_ships_the_project_files(sdist):
    entries = set(sdist_entries(sdist))

    assert "LICENSE" in entries
    assert "README.md" in entries
    assert "PKG-INFO" in entries
    assert "pyproject.toml" in entries
    assert any(name.startswith("src/func_to_web/") for name in entries)

    for asset in sorted(EXPECTED_ASSETS):
        assert f"src/func_to_web/{asset}" in entries


def test_sdist_assets_match_the_source_tree(sdist):
    packaged = assets_in(sdist_entries(sdist), "src/func_to_web/")
    on_disk = assets_on_disk()

    assert packaged == on_disk, (
        f"missing from the sdist: {sorted(on_disk - packaged)}; "
        f"unexpected in the sdist: {sorted(packaged - on_disk)}"
    )


def test_sdist_has_no_bytecode_caches_or_secrets(sdist):
    entries = sdist_entries(sdist)

    assert offending(entries, skip_prefixes=("src/func_to_web.egg-info/",)) == []
    assert not any(name.startswith("tests/") for name in entries)
    assert not any(name.endswith((".whl", ".tar.gz")) for name in entries)


def test_clean_install_imports_from_site_packages(installed_python, tmp_path):
    payload = run_in_venv(installed_python, IMPORT_PROBE, tmp_path)
    location = Path(payload["file"]).resolve()

    assert "site-packages" in location.parts
    assert not location.is_relative_to(ROOT)


def test_clean_install_reports_the_released_version(installed_python, tmp_path):
    payload = run_in_venv(installed_python, IMPORT_PROBE, tmp_path)

    assert payload["version"] == VERSION


def test_clean_install_exports_the_whole_public_api(installed_python, tmp_path):
    payload = run_in_venv(installed_python, IMPORT_PROBE, tmp_path)

    from func_to_web import __all__

    assert payload["missing_attribute"] == []
    assert payload["missing_star"] == []
    assert payload["exported"] == sorted(__all__)


def test_clean_install_builds_a_router(installed_python, tmp_path):
    payload = run_in_venv(installed_python, ROUTER_PROBE, tmp_path)

    assert payload["is_api_router"]
    assert payload["type"] == "APIRouter"
    assert "/demo/" in payload["routes"]
    assert "/doc" in payload["routes"]
    assert "/static/{name:path}" in payload["routes"]


def test_clean_install_renders_a_page_and_the_documentation(installed_python,
                                                            tmp_path):
    payload = run_in_venv(installed_python, PAGE_PROBE, tmp_path)

    assert payload["page_status"] == 200
    assert payload["page_has_root"]
    assert payload["doc_status"] == 200
    assert "demo" in payload["doc_text"]


def test_clean_install_serves_every_crawled_asset(installed_python, tmp_path):
    payload = run_in_venv(installed_python, CRAWL_PROBE, tmp_path)
    resources = payload["resources"]
    broken = {url: status for url, status in resources.items() if status != 200}

    assert broken == {}
    assert OWN_CRAWLED_ASSETS <= set(resources)
    assert len(resources) >= 20, sorted(resources)
