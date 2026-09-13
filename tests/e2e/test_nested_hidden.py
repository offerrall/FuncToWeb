import json
from dataclasses import dataclass
from urllib.parse import urlencode

import pytest

pytestmark = [pytest.mark.browser, pytest.mark.slow]


@dataclass
class Config:
    token: str = "new-token"
    name: str = "New"


def save(config: Config, items: list[Config], root: str = "root") -> str:
    return json.dumps({
        "config": vars(config), "items": [vars(item) for item in items], "root": root,
    })


def test_nested_visibility_keeps_prefill_and_new_items_in_submission(
    page, app_factory, live_server, console,
):
    origin = live_server(app_factory([save]))
    values = {
        "config": {"token": "abc", "name": "Demo"},
        "items": [{"token": "def", "name": "First"}],
        "root": "kept",
    }
    query = urlencode({
        "prefill": json.dumps(values),
        "hidden": json.dumps(["config.token", "items.*.token", "root"]),
    })
    page.goto(f"{origin}/save/?{query}")
    page.wait_for_selector("#fields .pth-field")
    tokens = page.locator(".pth-str input").filter(visible=False)
    assert tokens.count() == 3
    assert page.get_by_label("name", exact=True).nth(0).input_value() == "Demo"
    page.get_by_label("name", exact=True).nth(0).fill("Changed")
    page.locator(".pth-list-add").click()
    assert tokens.count() == 4
    assert page.get_by_label("name", exact=True).nth(2).is_visible()
    page.click("#submit")
    result = page.locator("#result .ftw-output-text .ftw-output-value")
    result.wait_for()
    values["config"]["name"] = "Changed"
    values["items"].append({"token": "new-token", "name": "New"})
    assert json.loads(result.text_content()) == values
    assert not console
