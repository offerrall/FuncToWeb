import json
import re
from typing import Annotated, get_args
from urllib.parse import urljoin

import pytest

from pytypehintweb import STATIC

from func_to_web import (
    OpenForm,
    Theme,
    WebFunction,
    WebFunctions,
    page_of,
    app_of,
    run,
)
from func_to_web.templates.index import index_of
from func_to_web.templates.theme import checked_theme
from func_to_web.web.router import STATIC_ROOTS

VALID_THEMES = ("system", "light", "dark")

NOT_STRINGS = (None, True, False, 0, 1, ["dark"], {"theme": "dark"})

INVALID_STRINGS = ("", "System", "SYSTEM", "auto", " light", "light ")

ROOT_TAGS = {
    "system": "<html>",
    "light": '<html data-pth-theme="light">',
    "dark": '<html data-pth-theme="dark">',
}

REMOVED_TOKENS = ("--pth-input-bg", "--pth-submit-bg", "--pth-color-scheme")

THEME_WORDS = ("theme", "cookie", "localstorage", "sessionstorage",
               "matchmedia", "prefers-color-scheme")

STORAGE_WORDS = ("localstorage", "sessionstorage", "cookie")


def edit_note(note_id: int, text: str = "draft") -> str:
    """Edit a note."""
    return text


def pick_note(
    note_id: int = 1,
) -> Annotated[dict, OpenForm(edit_note, hidden=("note_id",))]:
    """Pick a note."""
    return {"note_id": note_id, "text": "picked"}


def _captured_server(monkeypatch):
    import uvicorn

    captured = {}

    def fake_run(app, **options):
        captured["app"] = app
        captured["options"] = options

    monkeypatch.setattr(uvicorn, "run", fake_run)

    return captured


def _forbidden_server(monkeypatch):
    import uvicorn

    def fake_run(app, **options):
        raise AssertionError("uvicorn.run must not be reached")

    monkeypatch.setattr(uvicorn, "run", fake_run)


def _asset_names():
    names = []

    for root in STATIC_ROOTS:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                names.append(path.relative_to(root).as_posix())

    return sorted(set(names))


def _tokens_used(css):
    return set(re.findall(r"var\(\s*(--pth-[a-z0-9-]+)", css))


def _tokens_defined(css):
    return set(re.findall(r"(--pth-[a-z0-9-]+)\s*:", css))


@pytest.mark.parametrize("value", VALID_THEMES)
def test_checked_theme_returns_each_valid_value_unchanged(value):
    assert checked_theme(value) == value


def test_theme_declares_exactly_the_three_valid_values():
    assert get_args(Theme) == VALID_THEMES


@pytest.mark.parametrize("value", NOT_STRINGS)
def test_checked_theme_rejects_a_non_string_with_type_error(value):
    with pytest.raises(TypeError) as error:
        checked_theme(value)

    message = str(error.value)

    assert "theme" in message
    assert "str" in message


@pytest.mark.parametrize("value", INVALID_STRINGS)
def test_checked_theme_rejects_an_unknown_string_with_value_error(value):
    with pytest.raises(ValueError) as error:
        checked_theme(value)

    message = str(error.value)

    for name in VALID_THEMES:
        assert name in message


@pytest.mark.parametrize("value", NOT_STRINGS)
def test_app_of_rejects_a_non_string_theme_when_it_is_built(scalar, value):
    with pytest.raises(TypeError):
        app_of(scalar, theme=value)


@pytest.mark.parametrize("value", INVALID_STRINGS)
def test_app_of_rejects_an_unknown_theme_string_when_it_is_built(
    scalar,
    value,
):
    with pytest.raises(ValueError):
        app_of(scalar, theme=value)


@pytest.mark.parametrize("value", NOT_STRINGS)
def test_run_rejects_a_non_string_theme_before_starting_the_server(
    scalar,
    monkeypatch,
    value,
):
    _forbidden_server(monkeypatch)

    with pytest.raises(TypeError):
        run(scalar, theme=value)


@pytest.mark.parametrize("value", INVALID_STRINGS)
def test_run_rejects_an_unknown_theme_string_before_starting_the_server(
    scalar,
    monkeypatch,
    value,
):
    _forbidden_server(monkeypatch)

    with pytest.raises(ValueError):
        run(scalar, theme=value)


@pytest.mark.parametrize("theme", VALID_THEMES)
def test_run_gives_the_same_theme_to_the_index_and_to_every_page(
    scalar,
    monkeypatch,
    html_root,
    theme,
):
    from fastapi.testclient import TestClient

    captured = _captured_server(monkeypatch)

    run(scalar, theme=theme)

    with TestClient(captured["app"]) as client:
        assert html_root(client.get("/").text) == ROOT_TAGS[theme]
        assert html_root(client.get("/add/").text) == ROOT_TAGS[theme]


@pytest.mark.parametrize("value", NOT_STRINGS)
def test_page_of_rejects_a_non_string_theme(scalar, value):
    with pytest.raises(TypeError):
        page_of(WebFunction(scalar), theme=value)


@pytest.mark.parametrize("value", INVALID_STRINGS)
def test_page_of_rejects_an_unknown_theme_string(scalar, value):
    with pytest.raises(ValueError):
        page_of(WebFunction(scalar), theme=value)


@pytest.mark.parametrize("value", INVALID_STRINGS)
def test_page_of_still_rejects_an_unknown_theme_with_prefill(scalar, value):
    with pytest.raises(ValueError):
        page_of(WebFunction(scalar), prefill={"a": 5}, theme=value)


@pytest.mark.parametrize("value", NOT_STRINGS)
def test_page_of_still_rejects_a_non_string_theme_with_hidden(scalar, value):
    with pytest.raises(TypeError):
        page_of(WebFunction(scalar), hidden=["b"], theme=value)


def test_system_theme_leaves_the_html_tag_without_a_theme_attribute(
    scalar,
    client_factory,
    html_root,
):
    client = client_factory(scalar, theme="system")

    assert html_root(client.get("/add/").text) == ROOT_TAGS["system"]


@pytest.mark.parametrize("theme", ("light", "dark"))
def test_a_fixed_theme_writes_the_attribute_on_the_html_tag(
    scalar,
    client_factory,
    html_root,
    theme,
):
    client = client_factory(scalar, theme=theme)

    assert html_root(client.get("/add/").text) == ROOT_TAGS[theme]


def test_the_default_theme_of_a_router_is_system(
    scalar,
    client_factory,
    html_root,
):
    client = client_factory(scalar)

    assert html_root(client.get("/add/").text) == ROOT_TAGS["system"]


@pytest.mark.parametrize("theme", VALID_THEMES)
def test_the_served_page_body_carries_the_pth_root_class(
    scalar,
    client_factory,
    theme,
):
    client = client_factory(scalar, theme=theme)

    assert 'class="pth-root"' in client.get("/add/").text


@pytest.mark.parametrize("theme", VALID_THEMES)
@pytest.mark.parametrize("hook", ("data-theme=", ".light-mode", ".dark-mode"))
def test_the_served_page_carries_no_legacy_theme_hook(
    scalar,
    client_factory,
    theme,
    hook,
):
    client = client_factory(scalar, theme=theme)

    assert hook not in client.get("/add/").text


@pytest.mark.parametrize("theme", ("light", "dark"))
def test_an_opening_with_prefill_keeps_the_theme_of_the_space(
    scalar,
    client_factory,
    html_root,
    plan_of_page,
    theme,
):
    client = client_factory(scalar, theme=theme)
    body = client.get("/add/", params={"prefill": json.dumps({"a": 5})}).text
    defaults = {field["name"]: field["default"]
                for field in plan_of_page(body)["fields"]}

    assert defaults["a"] == 5
    assert html_root(body) == ROOT_TAGS[theme]


@pytest.mark.parametrize("theme", ("light", "dark"))
def test_an_opening_with_hidden_keeps_the_theme_of_the_space(
    scalar,
    client_factory,
    html_root,
    theme,
):
    client = client_factory(scalar, theme=theme)
    body = client.get("/add/", params={"hidden": json.dumps(["b"])}).text

    assert '["b"]' in body
    assert html_root(body) == ROOT_TAGS[theme]


@pytest.mark.parametrize("theme", ("light", "dark"))
def test_the_target_page_of_an_open_form_keeps_the_theme_of_the_space(
    client_factory,
    html_root,
    theme,
):
    client = client_factory([pick_note, edit_note], prefix="/tools",
                            theme=theme)
    result = client.post("/tools/pick_note/invoke", json={"note_id": 3})

    assert result.status_code == 200

    href = result.json()["result"]["href"]
    opening = client.get(urljoin("/tools/pick_note/", href))

    assert opening.status_code == 200
    assert html_root(opening.text) == ROOT_TAGS[theme]


@pytest.mark.parametrize("theme", ("light", "dark"))
def test_every_function_of_the_space_carries_the_same_theme(
    scalar,
    printing,
    failing,
    client_factory,
    html_root,
    theme,
):
    client = client_factory([scalar, printing, failing], theme=theme)

    for slug in ("add", "chatty", "boom"):
        assert html_root(client.get(f"/{slug}/").text) == ROOT_TAGS[theme]


@pytest.mark.parametrize("theme", (None, "system"))
def test_the_cached_base_html_is_reused_for_system_without_prefill_or_hidden(
    scalar,
    theme,
):
    web_function = WebFunction(scalar)
    options = {} if theme is None else {"theme": theme}

    assert page_of(web_function, **options) is web_function.html


@pytest.mark.parametrize("theme", ("light", "dark"))
def test_a_fixed_theme_never_serves_the_cached_base_html(scalar, theme):
    web_function = WebFunction(scalar)
    page = page_of(web_function, theme=theme)

    assert page is not web_function.html
    assert page != web_function.html


@pytest.mark.parametrize(
    "options",
    ({"prefill": {"a": 5}}, {"hidden": ["b"]}),
)
def test_prefill_or_hidden_never_serves_the_cached_base_html(scalar, options):
    web_function = WebFunction(scalar)

    assert page_of(web_function, **options) != web_function.html


@pytest.mark.parametrize("theme", VALID_THEMES)
def test_the_space_index_carries_the_same_theme_attribute(
    scalar,
    html_root,
    theme,
):
    space = WebFunctions((WebFunction(scalar),))

    assert html_root(index_of(space, "", theme)) == ROOT_TAGS[theme]


def test_the_space_index_defaults_to_the_system_theme(scalar, html_root):
    space = WebFunctions((WebFunction(scalar),))

    assert html_root(index_of(space, "")) == ROOT_TAGS["system"]


@pytest.mark.parametrize("value", INVALID_STRINGS)
def test_the_space_index_rejects_an_unknown_theme_string(scalar, value):
    space = WebFunctions((WebFunction(scalar),))

    with pytest.raises(ValueError):
        index_of(space, "", value)


@pytest.mark.parametrize("name", [n for n in _asset_names()
                                  if n.endswith(".js")])
def test_no_served_javascript_asset_selects_or_stores_a_theme(
    scalar,
    client_factory,
    name,
):
    client = client_factory(scalar)
    response = client.get(f"/static/{name}")

    assert response.status_code == 200

    body = response.text.lower()

    for word in THEME_WORDS:
        assert word not in body


@pytest.mark.parametrize("name", [n for n in _asset_names()
                                  if n.endswith((".js", ".css"))])
def test_no_served_asset_uses_local_storage_or_cookies(
    scalar,
    client_factory,
    name,
):
    client = client_factory(scalar)
    response = client.get(f"/static/{name}")

    assert response.status_code == 200

    body = response.text.lower()

    for word in STORAGE_WORDS:
        assert word not in body


@pytest.mark.parametrize("theme", VALID_THEMES)
def test_no_served_page_uses_local_storage_or_cookies(
    scalar,
    client_factory,
    theme,
):
    client = client_factory(scalar, theme=theme)
    body = client.get("/add/").text.lower()

    for word in STORAGE_WORDS:
        assert word not in body


def test_page_css_only_uses_tokens_that_widgets_css_defines(
    scalar,
    client_factory,
):
    client = client_factory(scalar)
    page_css = client.get("/static/page.css").text
    widgets_css = (STATIC / "widgets.css").read_text(encoding="utf-8")
    used = _tokens_used(page_css)

    assert used
    assert used <= _tokens_defined(widgets_css)


def test_page_css_defines_no_theme_token_of_its_own(scalar, client_factory):
    client = client_factory(scalar)

    assert _tokens_defined(client.get("/static/page.css").text) == set()


@pytest.mark.parametrize("token", REMOVED_TOKENS)
def test_page_css_does_not_use_a_removed_token(scalar, client_factory, token):
    client = client_factory(scalar)

    assert token not in client.get("/static/page.css").text
