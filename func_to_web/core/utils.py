from pathlib import Path
import base64
import re
from typing import Any

from pytypeinputweb import list_css_variables as _pti_css_variables
from pytypeinputweb import get_css, get_js

from .constants import INTERNAL_STATIC_DIR, STATIC_DIR, INTERNAL_STATIC_DIR

_MIME_TYPES = {
    ".ico": "image/x-icon",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
}

_CSS_VAR_DEF_RE = re.compile(r"(--functoweb-[\w-]+)\s*:")
_SLUG_RE = re.compile(r"^[a-z0-9_-]+$")

def create_pytypeinput_assets() -> dict[str, Path]:
    """Create CSS and JS assets."""
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    css_file = STATIC_DIR / "styles.css"
    js_file = STATIC_DIR / "scripts.js"

    pytypeinput_css = get_css()
    pytypeinput_js = get_js()

    functoweb_css = ""
    css_dir = INTERNAL_STATIC_DIR / "css"
    if css_dir.exists():
        for css_path in sorted(css_dir.glob("*.css")):
            functoweb_css += css_path.read_text(encoding='utf-8') + "\n\n"

    functoweb_js = ""
    js_dir = INTERNAL_STATIC_DIR / "js"
    if js_dir.exists():
        for js_path in sorted(js_dir.glob("*.js")):
            functoweb_js += js_path.read_text(encoding='utf-8') + "\n\n"

    combined_css = f"{pytypeinput_css}\n\n{functoweb_css}"
    combined_js = f"{pytypeinput_js}\n\n{functoweb_js}"

    css_file.write_text(combined_css, encoding='utf-8')
    js_file.write_text(combined_js, encoding='utf-8')

    return {'css': css_file, 'js': js_file}

def print_beta_warning():
    from .. import __version__

    """Print beta version warning message."""
    print("=" * 70)
    print(f"FuncToWeb {__version__} BETA")
    print("=" * 70)
    print("This is a major rewrite and introduces breaking changes.")
    print()
    print("If something that worked before no longer works:")
    print("   • It may require small updates to your code")
    print("   • Most APIs remain similar, but some features have changed")
    print("     (e.g. groups structure, run() parameters)")
    print()
    print("If you encounter actual bugs:")
    print("   • Report them: https://github.com/offerrall/functoweb/issues")
    print()
    print("Need stability?")
    print("   • pip install func-to-web==0.9.14")
    print()
    print("Thank you for testing!")
    print("=" * 70)
    print()

def encode_favicon_to_base64(favicon_path: str | Path) -> str:
    """Encode a favicon file to base64 data URI."""
    path = Path(favicon_path)

    if not path.exists():
        raise FileNotFoundError(f"Favicon not found: {path}")

    favicon_b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    mime_type = _MIME_TYPES.get(path.suffix.lower(), "image/x-icon")
    return f"data:{mime_type};base64,{favicon_b64}"


def slugify(name: str) -> str:
    """Convert a name to a URL-friendly slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def validate_slug(slug: str) -> None:
    """Validate that a slug contains only valid characters."""
    if not _SLUG_RE.match(slug):
        raise ValueError(
            f"Invalid slug '{slug}'. "
            f"Slug must contain only lowercase letters, digits, underscores, and hyphens."
        )


def detect_input_type(func_input: Any) -> str:
    """Detect if input is 'single', 'multiple', or 'grouped'."""
    if isinstance(func_input, dict):
        return "grouped"
    elif isinstance(func_input, list):
        return "multiple"
    return "single"


def list_css_variables() -> list[str]:
    """List all available CSS variables for customization."""
    pti_vars = list(_pti_css_variables().keys())

    ftw_vars: list[str] = []
    variables_css_path = INTERNAL_STATIC_DIR / "css" / "01-variables.css"

    if variables_css_path.exists():
        text = variables_css_path.read_text(encoding="utf-8")
        ftw_vars = sorted(set(_CSS_VAR_DEF_RE.findall(text)))

    return sorted(pti_vars + ftw_vars)


def validate_css_vars(css_vars: dict[str, str] | None) -> None:
    """Validate that CSS variables are valid."""
    if not css_vars:
        return

    valid_vars = set(list_css_variables())
    invalid_vars = [v for v in css_vars if v not in valid_vars]

    if invalid_vars:
        raise ValueError(
            f"Invalid CSS variable(s): {', '.join(invalid_vars)}\n"
            f"Use list_css_variables() to see valid options."
        )