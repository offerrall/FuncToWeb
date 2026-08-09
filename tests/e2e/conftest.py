import asyncio

import pytest
from starlette.middleware.base import BaseHTTPMiddleware

from shared import warm_uvicorn

warm_uvicorn()

READY = "#fields .pth-field"

TIMEOUT = 15000


@pytest.fixture(scope="session")
def playwright_engine():
    api = pytest.importorskip("playwright.sync_api",
                              reason="playwright is not installed")

    with api.sync_playwright() as engine:
        yield engine


@pytest.fixture(scope="session")
def browser(playwright_engine):
    from playwright.sync_api import Error

    try:
        instance = playwright_engine.chromium.launch()
    except Error as error:
        pytest.skip(f"no playwright browser available: {error}")

    yield instance

    instance.close()


@pytest.fixture
def page(browser):
    context = browser.new_context()
    context.set_default_timeout(TIMEOUT)

    opened = context.new_page()

    yield opened

    context.close()


@pytest.fixture
def console(page):
    messages = []

    page.on("console", lambda message: messages.append(message))
    page.on("pageerror", lambda error: messages.append(error))

    return messages


@pytest.fixture
def open_page(page, app_factory, live_server):
    def opened(fns, slug, *, prefix="", delay_uploads=0.0, **options):
        app = app_factory(fns, prefix=prefix, **options)

        if delay_uploads:
            async def held(request, call_next):
                if request.url.path.endswith("/upload"):
                    await asyncio.sleep(delay_uploads)

                return await call_next(request)

            app.add_middleware(BaseHTTPMiddleware, dispatch=held)

        origin = live_server(app)

        page.goto(f"{origin}{prefix}/{slug}/")
        page.wait_for_selector(READY)

        return page

    return opened


@pytest.fixture
def local_file(tmp_path):
    def make(name="local.txt", content=b"local bytes"):
        path = tmp_path / "chosen"
        path.mkdir(exist_ok=True)
        target = path / name
        target.write_bytes(content)

        return target

    return make


@pytest.fixture
def drop_file(page):
    def drop(selector, path, media_type="text/plain"):
        page.eval_on_selector(
            selector,
            """(input, payload) => {
                const bytes = Uint8Array.from(payload.data);
                const file = new File([bytes], payload.name,
                                      { type: payload.type });
                const transfer = new DataTransfer();

                transfer.items.add(file);

                input.dispatchEvent(new DragEvent("dragover", {
                    bubbles: true, cancelable: true, dataTransfer: transfer,
                }));
                input.dispatchEvent(new DragEvent("drop", {
                    bubbles: true, cancelable: true, dataTransfer: transfer,
                }));

                input.files = transfer.files;
                input.dispatchEvent(new Event("change", { bubbles: true }));
            }""",
            {
                "name": path.name,
                "type": media_type,
                "data": list(path.read_bytes()),
            },
        )

    return drop
