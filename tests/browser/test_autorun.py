import pytest

CASES = [
    "runs",
    "prefilled",
    "waits",
    "incomplete",
    "completed",
    "modal",
]


def add(a: int = 1, b: int = 2) -> str:
    """Adds two numbers."""
    return str(a + b)


def needs(a: int, b: int = 2) -> str:
    """Needs a value nobody gave."""
    return str(a + b)


SPACE = [add, needs]


@pytest.mark.browser
@pytest.mark.slow
@pytest.mark.parametrize("case", CASES)
def test_a_page_runs_itself_in_a_real_browser(verify, app_factory, case):
    verdict, log = verify(app_factory(SPACE), "autorun.html", case)

    assert verdict == "PASS", log
