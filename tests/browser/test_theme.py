import pytest

SYSTEM_DARK = ("--blink-settings=preferredColorScheme=0",)
SYSTEM_LIGHT = ("--blink-settings=preferredColorScheme=1",)

CASES = [
    ("system", SYSTEM_LIGHT, "system_light"),
    ("system", SYSTEM_DARK, "system_dark"),
    ("light", SYSTEM_DARK, "forced_light"),
    ("dark", SYSTEM_LIGHT, "forced_dark"),
]


def paint(note: str = "hi") -> str:
    """Answers with what it was given."""
    return note


@pytest.mark.browser
@pytest.mark.slow
@pytest.mark.parametrize("theme, flags, case", CASES,
                         ids=[case for _, _, case in CASES])
def test_the_theme_resolves_in_a_real_browser(verify, app_factory,
                                              theme, flags, case):
    verdict, log = verify(app_factory(paint, theme=theme), "theme.html", case,
                          flags=flags)

    assert verdict == "PASS", log
