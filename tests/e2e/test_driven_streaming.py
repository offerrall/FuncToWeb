from time import sleep

import pytest

pytestmark = [pytest.mark.browser, pytest.mark.slow]

STDOUT = "#result .ftw-output-stdout .ftw-output-value"

RUNNING = "#result .ftw-output-running"

TEXT = "#result .ftw-output-text .ftw-output-value"

ERROR = "#result .ftw-output-error .ftw-output-value"


def chatty(lines: int = 3) -> str:
    """Prints while it works."""
    for index in range(lines):
        print(f"line {index}", flush=True)
        sleep(0.35)

    return "finished"


def quiet(a: int = 1) -> str:
    """Prints nothing."""
    sleep(0.4)
    return f"quiet {a}"


def noisy_failure(a: int = 1) -> str:
    """Prints and then raises."""
    print("before the crash", flush=True)
    sleep(0.2)
    raise RuntimeError("crashed")


def test_printed_lines_appear_before_the_result(open_page):
    page = open_page(chatty, "chatty")

    page.click("#submit")
    page.wait_for_selector(STDOUT)

    first = page.text_content(STDOUT)

    assert page.locator(TEXT).count() == 0

    page.wait_for_function(
        "() => document.querySelector("
        "'#result .ftw-output-stdout .ftw-output-value')"
        ".textContent.includes('line 2')")

    grown = page.text_content(STDOUT)

    assert grown.startswith(first)
    assert len(grown) > len(first)


def test_the_running_mark_is_visible_until_the_result_arrives(open_page):
    page = open_page(quiet, "quiet")

    page.click("#submit")
    page.wait_for_selector(RUNNING)

    assert page.is_visible(RUNNING)

    page.wait_for_selector(TEXT)

    assert page.locator(RUNNING).count() == 0
    assert page.text_content(TEXT) == "quiet 1"


def test_the_final_result_keeps_what_was_printed(open_page):
    page = open_page(chatty, "chatty")

    page.click("#submit")
    page.wait_for_selector(TEXT)

    assert page.text_content(TEXT) == "finished"
    assert page.text_content(STDOUT).splitlines() == [
        "line 0", "line 1", "line 2",
    ]
    assert page.locator(RUNNING).count() == 0


def test_a_crash_keeps_the_lines_printed_before_it(open_page):
    page = open_page(noisy_failure, "noisy_failure")

    page.click("#submit")
    page.wait_for_selector(ERROR)

    assert "before the crash" in page.text_content(STDOUT)
    assert "RuntimeError: crashed" in page.text_content(ERROR)


def test_prints_are_silenced_when_the_space_says_so(open_page):
    page = open_page(chatty, "chatty", capture_prints=False)

    page.click("#submit")
    page.wait_for_selector(TEXT)

    assert page.locator(STDOUT).count() == 0
    assert page.text_content(TEXT) == "finished"


def test_a_second_run_starts_from_an_empty_output(open_page, page):
    page = open_page(chatty, "chatty")
    widest = []

    page.expose_binding("recordWidth",
                        lambda _source, value: widest.append(value))
    page.evaluate("""
        () => {
            new MutationObserver(() => {
                const out = document.querySelector(
                    "#result .ftw-output-stdout .ftw-output-value");

                if (out !== null) {
                    window.recordWidth(
                        out.textContent.split("\\n").filter(Boolean).length);
                }
            }).observe(document.getElementById("result"),
                       { childList: true, subtree: true,
                         characterData: true });
        }
    """)

    page.click("#submit")
    page.wait_for_selector(TEXT)
    page.click("#submit")
    page.wait_for_function(
        "() => !document.querySelector('#submit').disabled "
        "&& document.querySelector('#result .ftw-output-text') !== null")

    assert page.text_content(STDOUT).splitlines() == [
        "line 0", "line 1", "line 2",
    ]
    assert max(widest) == 3
