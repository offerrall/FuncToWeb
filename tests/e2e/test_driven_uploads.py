import os
from pathlib import Path
from typing import Annotated

import pytest

import func_to_web.web.upload as upload_module
from func_to_web import IsPathFile

pytestmark = [pytest.mark.browser, pytest.mark.slow]

TxtFile = Annotated[str, IsPathFile(extensions=(".txt",))]

MODAL = ".ftw-upload"

NAME = ".ftw-upload-name"

PERCENT = ".ftw-upload-percent"

COUNT = ".ftw-upload-count"

UPLOAD_ERROR = ".ftw-upload-error"

CLOSE = ".ftw-upload-close"

TEXT = "#result .ftw-output-text .ftw-output-value"

WATCH_PERCENT = """
() => {
    window.__percents = [];
    window.__modalShown = false;

    const modal = document.querySelector(".ftw-upload");
    const percent = modal.querySelector(".ftw-upload-percent");

    new MutationObserver(() => {
        window.__percents.push(percent.textContent);

        if (!modal.hidden) window.__modalShown = true;
    }).observe(modal, {
        subtree: true,
        childList: true,
        characterData: true,
        attributes: true,
    });
}
"""


class SwitchableReplace:

    def __init__(self):
        self.denied = True

    def replace(self, source, destination):
        if self.denied:
            raise PermissionError(13, "Permission denied")

        os.replace(source, destination)


def take_one(document: TxtFile) -> str:
    """Reads one file."""
    return Path(document).read_text(encoding="utf-8")


def take_many(documents: list[TxtFile]) -> str:
    """Reads several files."""
    return "|".join(Path(item).read_text(encoding="utf-8")
                    for item in documents)


def take_one_repeated(document: TxtFile, times: int = 1) -> str:
    """Reads one file as many times as asked."""
    return Path(document).read_text(encoding="utf-8") * times


def file_input(page, index=0):
    return page.locator("input[type=file]").nth(index)


def field_input(page, label):
    return page.locator(f".pth-field:has(label:text-is('{label}')) input")


def test_choosing_a_file_and_submitting_uploads_and_runs(open_page,
                                                         local_file,
                                                         uploads_dir):
    page = open_page(take_one, "take_one")
    chosen = local_file("report.txt", b"chosen content")

    file_input(page).set_input_files(chosen)
    page.click("#submit")

    assert page.text_content(TEXT) == "chosen content"

    stored = [entry for entry in uploads_dir.iterdir()]

    assert len(stored) == 1
    assert stored[0].read_bytes() == b"chosen content"
    assert stored[0].name.endswith(".txt")


def test_a_dropped_file_is_uploaded_like_a_chosen_one(open_page, drop_file,
                                                      local_file,
                                                      uploads_dir):
    page = open_page(take_one, "take_one")
    chosen = local_file("dropped.txt", b"dropped content")

    drop_file("input[type=file]", chosen)
    page.click("#submit")

    assert page.text_content(TEXT) == "dropped content"
    assert [entry.read_bytes() for entry in uploads_dir.iterdir()] == [
        b"dropped content"
    ]


def test_the_upload_modal_names_the_file_while_it_travels(open_page,
                                                          local_file):
    page = open_page(take_one, "take_one", delay_uploads=1.5)
    chosen = local_file("slowly.txt", b"x" * 2048)

    file_input(page).set_input_files(chosen)
    page.click("#submit")

    page.wait_for_selector(f"{MODAL}:not([hidden])")

    assert page.is_visible(".ftw-upload-dialog[aria-modal='true']")
    assert page.text_content(NAME) == "slowly.txt"
    assert page.text_content(COUNT) == "1 of 1"
    assert page.is_disabled("#submit")

    page.wait_for_selector(TEXT)

    assert page.is_hidden(MODAL)
    assert page.is_enabled("#submit")


def test_the_progress_only_moves_forward_and_ends_at_a_hundred(open_page,
                                                               local_file):
    page = open_page(take_one, "take_one")
    chosen = local_file("big.txt", b"x" * (4 * 1024 * 1024))

    page.evaluate(WATCH_PERCENT)

    file_input(page).set_input_files(chosen)
    page.click("#submit")
    page.wait_for_selector(TEXT)

    percents = [int(value.rstrip("%"))
                for value in page.evaluate("() => window.__percents")
                if value.endswith("%")]

    assert page.evaluate("() => window.__modalShown") is True
    assert percents == sorted(percents)
    assert percents[-1] == 100


def test_several_files_are_uploaded_one_by_one(open_page, local_file,
                                               uploads_dir):
    page = open_page(take_many, "take_many", delay_uploads=0.4)

    file_input(page).set_input_files([
        local_file("one.txt", b"one"),
        local_file("two.txt", b"two"),
    ])

    counts = []
    names = []

    page.expose_binding("recordStep",
                        lambda _source, count, name: (counts.append(count),
                                                      names.append(name)))
    page.evaluate("""
        () => {
            const modal = document.querySelector(".ftw-upload");
            const count = modal.querySelector(".ftw-upload-count");
            const name = modal.querySelector(".ftw-upload-name");

            new MutationObserver(() => {
                if (!modal.hidden) {
                    window.recordStep(count.textContent, name.textContent);
                }
            }).observe(modal, { childList: true, characterData: true,
                                subtree: true, attributes: true });
        }
    """)

    page.click("#submit")
    page.wait_for_selector(TEXT)

    assert page.text_content(TEXT) == "one|two"
    assert sorted(set(counts)) == ["1 of 2", "2 of 2"]
    assert sorted(set(names)) == ["one.txt", "two.txt"]
    assert len(list(uploads_dir.iterdir())) == 2


def test_a_refused_upload_shows_the_server_message_and_stays_open(open_page,
                                                                  local_file):
    page = open_page(take_one, "take_one", max_upload_bytes=8)
    chosen = local_file("toolarge.txt", b"x" * 64)

    file_input(page).set_input_files(chosen)
    page.click("#submit")

    page.wait_for_selector(f"{UPLOAD_ERROR}:not([hidden])")

    message = page.text_content(UPLOAD_ERROR)

    assert message.startswith("Upload failed: toolarge.txt")
    assert "exceeds the maximum size of 8 bytes" in message
    assert page.is_visible(CLOSE)
    assert page.locator(TEXT).count() == 0


def test_escape_closes_the_failed_upload_modal(open_page, local_file):
    page = open_page(take_one, "take_one", max_upload_bytes=8)

    file_input(page).set_input_files(local_file("toolarge.txt", b"x" * 64))
    page.click("#submit")
    page.wait_for_selector(f"{UPLOAD_ERROR}:not([hidden])")

    page.keyboard.press("Escape")

    assert page.is_hidden(MODAL)


def test_the_close_button_hides_the_failed_upload_modal(open_page, local_file):
    page = open_page(take_one, "take_one", max_upload_bytes=8)

    file_input(page).set_input_files(local_file("toolarge.txt", b"x" * 64))
    page.click("#submit")
    page.wait_for_selector(f"{UPLOAD_ERROR}:not([hidden])")

    page.click(CLOSE)

    assert page.is_hidden(MODAL)


def test_a_server_failure_is_retried_by_pressing_submit_again(open_page,
                                                              local_file,
                                                              uploads_dir,
                                                              monkeypatch):
    page = open_page(take_one, "take_one")
    chosen = local_file("retried.txt", b"retried content")
    switch = SwitchableReplace()

    monkeypatch.setattr(upload_module, "os", switch)

    file_input(page).set_input_files(chosen)
    page.click("#submit")
    page.wait_for_selector(f"{UPLOAD_ERROR}:not([hidden])")

    assert list(uploads_dir.iterdir()) == []

    switch.denied = False
    page.click(CLOSE)
    page.click("#submit")

    assert page.text_content(TEXT) == "retried content"
    assert [entry.read_bytes() for entry in uploads_dir.iterdir()] == [
        b"retried content"
    ]


def test_a_confirmed_upload_is_not_sent_again(open_page, local_file,
                                              uploads_dir, page):
    page = open_page(take_one, "take_one")
    sent = []

    def counted(route):
        sent.append(route.request.url)
        route.continue_()

    page.route("**/upload", counted)

    file_input(page).set_input_files(local_file("once.txt", b"once"))
    page.click("#submit")
    page.wait_for_selector(TEXT)

    page.click("#submit")
    page.wait_for_function(
        "() => !document.querySelector('#submit').disabled")

    assert len(sent) == 1
    assert page.text_content(TEXT) == "once"


def test_changing_another_parameter_never_uploads_the_file_again(open_page,
                                                                 local_file,
                                                                 uploads_dir):
    page = open_page(take_one_repeated, "take_one_repeated")
    sent = []

    def counted(route):
        sent.append(route.request.url)
        route.continue_()

    page.route("**/upload", counted)

    file_input(page).set_input_files(local_file("big.txt", b"ab"))

    outputs = []

    for times in ("1", "2", "3"):
        field_input(page, "times").fill(times)
        page.click("#submit")
        page.wait_for_function(
            "() => !document.querySelector('#submit').disabled")
        outputs.append(page.text_content(TEXT))

    assert outputs == ["ab", "abab", "ababab"]
    assert len(sent) == 1
    assert len(list(uploads_dir.iterdir())) == 1
