import json

from jinja2 import Environment, FileSystemLoader
from pytypeinput import ParamMetadata

from .core.constants import TEMPLATES_DIR
from .models import NormalizedInput, FunctionMetadata


# Shared Jinja environment (templates are static → no auto reload)
_jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    auto_reload=False
)


def _count_visible_items(navigation_data: list) -> int:
    """Count visible (non-hidden) functions in the nav tree."""
    count = 0
    for item in navigation_data or []:
        if item["type"] == "function" and not item.get("hidden"):
            count += 1
        elif item["type"] != "function":
            count += _count_visible_items(item.get("children", []))
    return count


def render_page(
    params: list[ParamMetadata],
    meta: FunctionMetadata,
    app_input: NormalizedInput,
    base_url: str = ""
) -> str:
    """Render a function page (form + layout)."""
    # Frontend builds the form from serialized param metadata
    params_json = json.dumps([p.to_dict() for p in params])

    form_html = _jinja_env.get_template("form.html").render(
        title=meta.name,
        description=meta.description,
        action=f"{base_url}/submit",
        params_json=params_json,
    )

    # Hide sidebar if there are fewer than 2 visible functions to navigate to
    navigation_data = app_input.navigation_data
    if _count_visible_items(navigation_data) < 2:
        navigation_data = None

    return _jinja_env.get_template("page.html").render(
        page_title=meta.name,
        form_html=form_html,
        css_vars=app_input.css_vars,
        favicon=app_input.favicon_data_uri,
        navigation_data=navigation_data,
    )


def render_index(app_input: NormalizedInput) -> str:
    """Render the index page (multi-function mode)."""
    return _jinja_env.get_template("index.html").render(
        page_title=app_input.title,
        items=app_input.navigation_data,
        css_vars=app_input.css_vars,
        favicon=app_input.favicon_data_uri,
        navigation_data=app_input.navigation_data,
    )