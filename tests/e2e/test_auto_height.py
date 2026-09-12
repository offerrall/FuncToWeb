import pytest
from starlette.responses import HTMLResponse

pytestmark = [pytest.mark.browser, pytest.mark.slow]


def report(lines: int = 1) -> str:
    return "\n".join("A line of the report" for _ in range(lines))


@pytest.mark.parametrize("modal", [False, True])
def test_embedded_page_grows_shrinks_and_modal_stays_in_view(
    page, app_factory, live_server, modal,
):
    app = app_factory(report)
    app.add_route("/host", lambda request: HTMLResponse('<div id="slot"></div>'))
    origin = live_server(app)
    page.set_viewport_size({"width": 1000, "height": 800})
    page.goto(f"{origin}/host")
    page.evaluate("""async (modal) => {
        const sdk = await import('/static/sdk.js');
        window.opened = modal ? sdk.openModal('/report') : null;
        window.frame = modal ? opened.iframe : sdk.embed('#slot', '/report');
    }""", modal)
    page.wait_for_function("""() => {
        const body = frame.contentDocument?.body;
        return body && Math.abs(frame.getBoundingClientRect().height -
            Math.ceil(body.getBoundingClientRect().height)) <= 1;
    }""")
    initial = page.evaluate("frame.getBoundingClientRect().height")
    child = page.frame_locator("iframe")
    child.locator("#fields input").fill("80")
    child.locator("#submit").click()
    page.wait_for_function("""() => {
        const body = frame.contentDocument.body;
        return body.getBoundingClientRect().height > 1000 &&
            (opened ? Math.abs(frame.getBoundingClientRect().height - 720) <= 1
                    : frame.getBoundingClientRect().height > 1000);
    }""")
    grown = page.evaluate("frame.getBoundingClientRect().height")
    assert grown > initial
    if modal:
        assert grown <= 720
        page.set_viewport_size({"width": 700, "height": 500})
        page.wait_for_function("frame.getBoundingClientRect().height <= 450")
    child.locator("#fields input").fill("1")
    child.locator("#submit").click()
    page.wait_for_function("""() => {
        const body = frame.contentDocument.body;
        return body.getBoundingClientRect().height < 450 &&
            Math.abs(frame.getBoundingClientRect().height -
                Math.ceil(body.getBoundingClientRect().height)) <= 1;
    }""")
    assert page.evaluate("frame.getBoundingClientRect().height") < grown


def test_auto_height_can_be_disabled(page, app_factory, live_server):
    app = app_factory(report)
    app.add_route("/host", lambda request: HTMLResponse("<div></div>"))
    page.goto(f"{live_server(app)}/host")
    page.evaluate("""async () => {
        const sdk = await import('/static/sdk.js');
        window.opened = sdk.openModal('/report', {height: 600, autoHeight: false});
    }""")
    page.frame_locator("iframe").locator("#submit").wait_for()
    assert page.evaluate("opened.iframe.getBoundingClientRect().height") == 600


def test_auto_height_works_across_origins(page, app_factory, live_server):
    app = app_factory(report)
    app.add_route("/host", lambda request: HTMLResponse('<div id="slot"></div>'))
    origin = live_server(app)
    page.goto(f"{origin}/host")
    page.evaluate("""async (url) => {
        const sdk = await import('/static/sdk.js');
        window.frame = sdk.embed('#slot', url);
    }""", origin.replace("127.0.0.1", "localhost") + "/report")
    page.wait_for_function("frame.style.height !== ''")
    child = page.frame_locator("iframe")
    child.locator("#submit").wait_for()
    assert page.evaluate("frame.contentDocument === null")
    assert page.evaluate("frame.getBoundingClientRect().height") > 100
