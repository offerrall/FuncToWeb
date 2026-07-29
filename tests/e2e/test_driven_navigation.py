from typing import Annotated
from urllib.parse import unquote

import pytest

from func_to_web import Download, OpenForm

pytestmark = [pytest.mark.browser, pytest.mark.slow]

TEXT = "#result .ftw-output-text .ftw-output-value"

FORM_LINK = "#result .ftw-output-form a"


def edit_product(product_id: int, name: str = "x", note: str = "") -> str:
    """Edits a product."""
    return f"{product_id}:{name}:{note}"


def select_product(product_id: int = 7) -> Annotated[
    dict,
    OpenForm(edit_product, hidden=("product_id",)),
]:
    """Selects a product."""
    return {"product_id": product_id, "name": "chosen"}


def pack(seed: int = 3) -> Annotated[bytes, Download("out.txt")]:
    """Packs a file."""
    return b"z" * seed


SPACE = [select_product, edit_product, pack]


def field_input(page, label):
    return page.locator(f".pth-field:has(label:text-is('{label}')) input")


@pytest.mark.parametrize("prefix", ["", "/tools"])
def test_open_form_navigates_to_the_target_page(open_page, prefix):
    page = open_page(SPACE, "select-product", prefix=prefix)

    page.click("#submit")
    page.wait_for_url("**/edit-product/**")

    assert page.text_content("h1") == "Edit product"
    assert f"{prefix}/edit-product/" in unquote(page.url)


def test_the_target_page_arrives_prefilled(open_page):
    page = open_page(SPACE, "select-product")

    page.click("#submit")
    page.wait_for_url("**/edit-product/**")
    page.wait_for_selector("#fields .pth-field")

    assert field_input(page, "name").input_value() == "chosen"


def test_the_hidden_field_is_not_shown_but_still_travels(open_page):
    page = open_page(SPACE, "select-product")

    page.click("#submit")
    page.wait_for_url("**/edit-product/**")
    page.wait_for_selector("#fields .pth-field")

    assert page.locator(".pth-field:has(label:text-is('product_id'))").count() == 0

    page.click("#submit")

    assert page.text_content(TEXT) == "7:chosen:"


def test_the_opening_link_is_drawn_before_the_jump(open_page, page):
    page = open_page(SPACE, "select-product")
    seen = []

    page.expose_binding("recordOpening",
                        lambda _source, href: seen.append(href))
    page.evaluate("""
        () => {
            new MutationObserver(() => {
                const link = document.querySelector(
                    "#result .ftw-output-form a");

                if (link !== null) window.recordOpening(link.getAttribute("href"));
            }).observe(document.getElementById("result"),
                       { childList: true, subtree: true });
        }
    """)

    with page.expect_navigation():
        page.click("#submit")

    assert seen != []
    assert seen[0].startswith("../edit-product/?prefill=")
    assert "edit-product" in unquote(page.url)


def test_the_prefilled_page_can_be_run_and_changed(open_page):
    page = open_page(SPACE, "select-product")

    page.click("#submit")
    page.wait_for_url("**/edit-product/**")
    page.wait_for_selector("#fields .pth-field")

    field_input(page, "name").fill("edited")
    page.click("#submit")

    assert page.text_content(TEXT) == "7:edited:"


def test_a_download_output_is_a_working_link(open_page):
    page = open_page(SPACE, "pack")

    page.click("#submit")
    page.wait_for_selector(FORM_LINK.replace("-form", "-download"))

    link = page.locator("#result .ftw-output-download a")

    assert link.get_attribute("download") == "out.txt"

    with page.expect_download() as caught:
        link.click()

    download = caught.value

    assert download.suggested_filename == "out.txt"

    stored = download.path()

    assert stored.read_bytes() == b"zzz"


def test_the_download_link_survives_a_second_run(open_page):
    page = open_page(SPACE, "pack")

    for expected in (b"zzz", b"zzzzz"):
        field_input(page, "seed").fill(str(len(expected)))
        page.click("#submit")
        page.wait_for_selector("#result .ftw-output-download a")

        with page.expect_download() as caught:
            page.click("#result .ftw-output-download a")

        assert caught.value.path().read_bytes() == expected
