from typing import Annotated

import pytest
from fastapi.responses import HTMLResponse

from func_to_web import Min

pytestmark = [pytest.mark.browser, pytest.mark.slow]

PREFIX = "/tools"

MODAL = ".ftw-modal"

CLOSE = ".ftw-modal .ftw-modal-close"

HOST = """<!doctype html>
<meta charset="utf-8">
<title>Host</title>
<h1>Host</h1>
<script type="module">
import { openModal } from "/tools/static/sdk.js";

const probe = {outcome: undefined, results: [], errors: [], modal: null};

probe.open = (url, options = {}) => {
    const modal = openModal(url, {
        ...options,
        onResult: (outputs) => probe.results.push(outputs),
        onError: (message) => probe.errors.push(message),
    });

    probe.modal = modal;
    modal.closed.then((outcome) => { probe.outcome = outcome; });

    return Object.keys(modal).sort();
};

window.probe = probe;
</script>
"""


def add(a: int, b: Annotated[int, Min(0)] = 2) -> str:
    """Adds two numbers."""
    return f"{a + b}"


def boom(a: int = 1) -> str:
    """Always raises."""
    raise RuntimeError("no luck")


@pytest.fixture
def host(page, app_factory, live_server):
    """A host page of its own, with the space mounted beside it."""
    def opened():
        app = app_factory([add, boom], prefix=PREFIX)

        @app.get("/", response_class=HTMLResponse)
        def home() -> str:
            return HOST

        page.goto(f"{live_server(app)}/")
        page.wait_for_function("window.probe !== undefined")

        return page

    return opened


def open_modal(page, slug, **options):
    keys = page.evaluate(
        "({url, options}) => window.probe.open(url, options)",
        {"url": f"{PREFIX}/{slug}", "options": options},
    )

    page.wait_for_selector(MODAL)

    return keys


def field(page, label):
    return page.frame_locator(f"{MODAL} iframe").locator(
        f".pth-field:has(label:text-is('{label}')) input")


def submit(page):
    page.frame_locator(f"{MODAL} iframe").locator("#submit").click()


def outcome(page):
    page.wait_for_function("window.probe.outcome !== undefined")

    return page.evaluate("window.probe.outcome")


def test_a_result_reaches_the_host_and_travels_in_closed(host):
    page = host()

    open_modal(page, "add")

    field(page, "a").fill("5")
    submit(page)

    page.wait_for_function("window.probe.results.length === 1")

    assert page.evaluate("window.probe.results[0]") == [
        {"type": "text", "value": "7"},
    ]
    assert page.locator(MODAL).count() == 1

    page.click(CLOSE)

    assert outcome(page) == {
        "completed": True,
        "results": [{"type": "text", "value": "7"}],
    }


def test_close_on_result_closes_the_modal_and_completes(host):
    page = host()

    open_modal(page, "add", closeOnResult=True)

    field(page, "a").fill("1")
    submit(page)

    assert outcome(page) == {
        "completed": True,
        "results": [{"type": "text", "value": "3"}],
    }
    assert page.locator(MODAL).count() == 0


def test_a_modal_dismissed_without_running_completes_nothing(host):
    page = host()

    open_modal(page, "add")
    page.click(CLOSE)

    assert outcome(page) == {"completed": False, "results": None}
    assert page.locator(MODAL).count() == 0


def test_a_failing_run_reaches_on_error_and_leaves_the_modal_open(host):
    page = host()

    open_modal(page, "boom", closeOnResult=True)
    submit(page)

    page.wait_for_function("window.probe.errors.length === 1")

    assert page.evaluate("window.probe.errors[0]") == "RuntimeError: no luck"
    assert page.evaluate("window.probe.results") == []
    assert page.locator(MODAL).count() == 1

    page.click(CLOSE)

    assert outcome(page) == {"completed": False, "results": None}


def test_a_url_that_does_not_exist_still_gives_a_usable_handle(host):
    page = host()

    keys = open_modal(page, "nope")

    assert keys == ["close", "closed", "element", "iframe"]

    page.click(CLOSE)

    assert outcome(page) == {"completed": False, "results": None}
    assert page.locator(MODAL).count() == 0
