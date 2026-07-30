import pytest

pytestmark = [pytest.mark.browser, pytest.mark.slow]

TABLE = "#result .ftw-output-table table"

IMAGE = "#result .ftw-output-image img"

TEXT = "#result .ftw-output-text .ftw-output-value"

pandas = pytest.importorskip("pandas")
PIL_Image = pytest.importorskip("PIL.Image")


def as_table(rows: int = 2):
    """Returns a table."""
    return pandas.DataFrame({"a": list(range(rows)), "b": ["x"] * rows})


def as_image(size: int = 4):
    """Returns an image."""
    return PIL_Image.new("RGB", (size, size), (10, 20, 30))


def as_several(size: int = 3):
    """Returns text, a table and an image."""
    return (
        "first",
        pandas.DataFrame({"n": list(range(size))}),
        PIL_Image.new("RGB", (size, size), (200, 100, 50)),
    )


SPACE = [as_table, as_image, as_several]


def test_a_table_is_drawn_with_headers_and_rows(open_page):
    page = open_page(SPACE, "as_table")

    page.click("#submit")
    page.wait_for_selector(TABLE)

    assert page.locator(f"{TABLE} thead th").all_text_contents() == ["a", "b"]
    assert page.locator(f"{TABLE} tbody tr").count() == 2
    assert page.locator(f"{TABLE} tbody tr").first.text_content() == "0x"


def test_the_table_csv_button_downloads_the_same_data(open_page):
    page = open_page(SPACE, "as_table")

    page.click("#submit")
    page.wait_for_selector(TABLE)

    with page.expect_download() as caught:
        page.click("#result .ftw-output-table .ftw-action:last-child")

    download = caught.value

    assert download.suggested_filename == "table.csv"
    assert download.path().read_text(encoding="utf-8").splitlines() == [
        "a,b", "0,x", "1,x",
    ]


def test_an_image_is_drawn_from_the_data_url(open_page):
    page = open_page(SPACE, "as_image")

    page.click("#submit")
    page.wait_for_selector(IMAGE)

    assert page.get_attribute(IMAGE, "src").startswith("data:image/png;base64,")
    assert page.evaluate(
        "() => { const img = document.querySelector("
        "'#result .ftw-output-image img'); "
        "return img.complete && img.naturalWidth; }") == 4


def test_several_outputs_keep_their_return_order(open_page):
    page = open_page(SPACE, "as_several")

    page.click("#submit")
    page.wait_for_selector(IMAGE)

    assert page.locator("#result > .ftw-output").count() == 3
    assert [
        element.get_attribute("class").split()[1]
        for element in page.locator("#result > .ftw-output").all()
    ] == ["ftw-output-text", "ftw-output-table", "ftw-output-image"]
    assert page.text_content(TEXT) == "first"


def test_a_second_run_replaces_every_output(open_page):
    page = open_page(SPACE, "as_table")

    page.click("#submit")
    page.wait_for_selector(TABLE)

    page.locator(".pth-field:has(label:text-is('rows')) input").fill("4")
    page.click("#submit")
    page.wait_for_function(
        "() => document.querySelectorAll("
        "'#result .ftw-output-table tbody tr').length === 4")

    assert page.locator("#result > .ftw-output").count() == 1
