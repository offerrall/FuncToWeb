import re
from html import escape
from importlib.resources import files

from func_to_web.models.functions import WebFunctions
from func_to_web.templates.page import _titled
from func_to_web.templates.theme import Theme, checked_theme, theme_attribute

INDEX_TEMPLATE: str = (
    files("func_to_web.templates")
    .joinpath("index.html")
    .read_text(encoding="utf-8")
)


def index_of(space: WebFunctions, prefix: str, theme: Theme = "system") -> str:
    items = []

    for web_function in space.functions:
        slug = escape(web_function.slug, quote=True)
        label = escape(_titled(web_function.name))
        description = (f"<span>{escape(web_function.description)}</span>"
                       if web_function.description else "")

        items.append(f'<a href="#{slug}" data-slug="{slug}">'
                     f"<strong>{label}</strong>{description}</a>")

    values = {
        "__ITEMS__": "\n    ".join(items),
        "__PREFIX__": prefix,
        "__TITLE__": escape(space.title),
        "__THEME__": theme_attribute(checked_theme(theme)),
    }

    return re.sub(
        r"__(?:ITEMS|PREFIX|TITLE|THEME)__",
        lambda match: values[match.group(0)],
        INDEX_TEMPLATE,
    )
