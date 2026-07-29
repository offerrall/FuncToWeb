import json
import re
from collections.abc import Iterable, Mapping
from html import escape
from importlib.resources import files
from typing import Any

from func_to_web.templates.theme import Theme, checked_theme, theme_attribute

PAGE_TEMPLATE: str = (
    files("func_to_web.templates")
    .joinpath("page.html")
    .read_text(encoding="utf-8")
)


def _embedded(value: Any) -> str:
    return json.dumps(value).replace("<", "\\u003c")


def labelled_plan(
    plan: Mapping[str, Any],
    *,
    name: str,
    description: str = "",
) -> dict[str, Any]:
    """Return a copy of plan carrying the metadata FuncToWeb publishes.

    The core builds name and description from fn.__name__ and fn.__doc__; a
    WebFunction may override both, and every published representation —page,
    index and /doc— must show the same pair. The original plan is not touched.
    """
    return {**plan, "name": name, "description": description or None}


def _titled(name: str) -> str:
    text = re.sub(r"\s+", " ", name.replace("_", " ")).strip()
    return text[:1].upper() + text[1:]


def page_from_plan(
    plan: Mapping[str, Any],
    *,
    name: str,
    description: str = "",
    hidden: Iterable[str] = (),
    theme: Theme = "system",
) -> str:
    values = {
        "PLAN_JSON": _embedded(
            labelled_plan(plan, name=name, description=description)
        ),
        "HIDDEN_JSON": _embedded(sorted(hidden)),
        "__THEME__": theme_attribute(checked_theme(theme)),
        "__TITLE__": escape(_titled(name)),
        "__META__": (
            f'<meta name="description" content="{escape(description, quote=True)}">'
            if description else ""
        ),
        "__DESCRIPTION__": (f"<p>{escape(description)}</p>"
                            if description else ""),
    }

    def render(match: re.Match[str]) -> str:
        indent, key = match.group(1), match.group(2)

        if key is None:
            return values[match.group(0)]

        return f"{indent}{values[key]}\n" if values[key] else ""

    return re.sub(
        r"([ \t]*)(__(?:META|DESCRIPTION)__)\n"
        r"|PLAN_JSON|HIDDEN_JSON|__TITLE__|__THEME__",
        render,
        PAGE_TEMPLATE,
    )
