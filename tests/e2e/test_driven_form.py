from time import sleep
from typing import Annotated

import pytest

from func_to_web import Max, Min

pytestmark = [pytest.mark.browser, pytest.mark.slow]

RESULT = "#result .ftw-output"

TEXT = "#result .ftw-output-text .ftw-output-value"

ERROR = "#result .ftw-output-error .ftw-output-value"


def add(a: int, b: Annotated[int, Min(0), Max(10)] = 2, note: str = "") -> str:
    """Adds two numbers."""
    return f"{a + b}{note}"


def slow_add(a: int = 1) -> str:
    """Takes its time."""
    sleep(0.6)
    return f"slow {a}"


def field_input(page, label):
    return page.locator(f".pth-field:has(label:text-is('{label}')) input")


def test_typing_and_clicking_submit_runs_the_function(open_page):
    page = open_page(add, "add")

    field_input(page, "a").fill("5")
    field_input(page, "b").fill("7")
    page.click("#submit")

    assert page.text_content(TEXT) == "12"


def test_the_page_shows_the_declared_name_and_description(open_page):
    page = open_page(add, "add")

    assert page.text_content("h1") == "Add"
    assert page.text_content("header p") == "Adds two numbers."


def test_a_missing_required_field_never_reaches_the_server(open_page, console):
    page = open_page(add, "add")

    page.click("#submit")

    assert "Complete: a" in page.text_content(ERROR)
    assert page.locator(TEXT).count() == 0


def test_a_value_out_of_bounds_is_refused_by_the_browser(open_page):
    page = open_page(add, "add")

    field_input(page, "a").fill("1")
    field_input(page, "b").fill("99")
    page.click("#submit")

    assert "Fix: b" in page.text_content(ERROR)


def test_the_number_buttons_change_the_value(open_page):
    page = open_page(add, "add")

    field_input(page, "a").fill("1")
    page.click(".pth-field:has(label:text-is('a')) "
               "button[aria-label='Increase']")
    page.click(".pth-field:has(label:text-is('a')) "
               "button[aria-label='Increase']")

    assert field_input(page, "a").input_value() == "3"

    page.click(".pth-field:has(label:text-is('a')) "
               "button[aria-label='Decrease']")

    assert field_input(page, "a").input_value() == "2"


def test_enter_in_a_text_field_does_not_submit_the_form(open_page):
    page = open_page(add, "add")

    field_input(page, "a").fill("1")
    field_input(page, "note").press("Enter")

    assert page.locator(RESULT).count() == 0


def test_several_runs_replace_the_previous_result(open_page):
    page = open_page(add, "add")

    for value, expected in (("1", "3"), ("10", "12"), ("100", "102")):
        field_input(page, "a").fill(value)
        page.click("#submit")
        page.wait_for_function(
            "expected => document.querySelector("
            "'#result .ftw-output-value')?.textContent === expected",
            arg=expected,
        )

        assert page.locator(RESULT).count() == 1


def test_submit_is_disabled_while_the_call_is_running(open_page):
    page = open_page(slow_add, "slow_add")

    page.click("#submit")

    assert page.is_disabled("#submit")

    page.wait_for_selector(TEXT)

    assert page.is_enabled("#submit")


def test_a_failing_function_shows_the_error_envelope(open_page, failing):
    page = open_page(failing, "boom")

    page.click("#submit")

    assert "RuntimeError: boom" in page.text_content(ERROR)


def test_the_page_runs_without_console_errors(open_page, console):
    page = open_page(add, "add")

    field_input(page, "a").fill("1")
    page.click("#submit")
    page.wait_for_selector(TEXT)

    assert [str(message) for message in console
            if getattr(message, "type", "") == "error"] == []
