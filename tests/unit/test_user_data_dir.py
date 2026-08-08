"""The default data directory, once the platform library was dropped.

Every test here fakes the platform and the home directory, so the three
branches are all read on whichever machine runs the suite: what used to be
covered by trusting a dependency is now covered by this file.
"""

import sys
from pathlib import Path

import pytest

from func_to_web.config import DATA_DIR, NAME, UPLOADS_DIR, _user_data_dir

VARIABLES = ("LOCALAPPDATA", "APPDATA", "XDG_DATA_HOME", "HOME", "USERPROFILE",
             "HOMEDRIVE", "HOMEPATH")

BLANK = ("", " ", "   ", "\t")


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A home of our own, with no variable of the real one left standing."""
    made = tmp_path / "home"
    made.mkdir()

    for variable in VARIABLES:
        monkeypatch.delenv(variable, raising=False)

    monkeypatch.setattr(Path, "home", staticmethod(lambda: made))

    return made


@pytest.fixture
def on(monkeypatch):
    def choose(system):
        monkeypatch.setattr("func_to_web.config.platform", system)

    return choose


def test_windows_takes_the_local_appdata_variable(on, home, monkeypatch):
    on("win32")
    monkeypatch.setenv("LOCALAPPDATA", r"D:\Profiles\ana\AppData\Local")

    assert _user_data_dir("App") == Path(r"D:\Profiles\ana\AppData\Local/App")


def test_windows_falls_back_to_the_home_when_the_variable_is_absent(on, home):
    on("win32")

    assert _user_data_dir("App") == home / "AppData" / "Local" / "App"


@pytest.mark.parametrize("value", BLANK)
def test_windows_falls_back_to_the_home_when_the_variable_is_empty(
    on, home, monkeypatch, value
):
    # An empty variable is no answer, and joining it would silently hand back
    # a relative path that resolves against the working directory.
    on("win32")
    monkeypatch.setenv("LOCALAPPDATA", value)

    assert _user_data_dir("App") == home / "AppData" / "Local" / "App"


def test_windows_ignores_the_roaming_variable(on, home, monkeypatch):
    # Uploads are working files of this machine, not something to sync into
    # a roaming profile.
    on("win32")
    monkeypatch.setenv("APPDATA", r"D:\Roaming")
    monkeypatch.setenv("LOCALAPPDATA", r"D:\Local")

    assert _user_data_dir("App") == Path(r"D:\Local/App")


def test_macos_uses_application_support_under_the_home(on, home):
    on("darwin")

    assert _user_data_dir("App") == home / "Library" / "Application Support" / "App"


def test_macos_ignores_the_xdg_variable(on, home, monkeypatch):
    on("darwin")
    monkeypatch.setenv("XDG_DATA_HOME", "/srv/data")

    assert _user_data_dir("App") == home / "Library" / "Application Support" / "App"


@pytest.mark.parametrize("system", ("linux", "freebsd", "openbsd", "sunos5"))
def test_every_other_system_follows_the_xdg_variable(on, home, monkeypatch,
                                                      system):
    on(system)
    monkeypatch.setenv("XDG_DATA_HOME", "/srv/data")

    assert _user_data_dir("App") == Path("/srv/data/App")


def test_linux_falls_back_to_local_share_when_the_variable_is_absent(on, home):
    on("linux")

    assert _user_data_dir("App") == home / ".local" / "share" / "App"


@pytest.mark.parametrize("value", BLANK)
def test_linux_falls_back_to_local_share_when_the_variable_is_blank(
    on, home, monkeypatch, value
):
    # The XDG spec says a variable set to an empty value counts as unset, and
    # whitespace is what a shell leaves behind when it exports nothing.
    on("linux")
    monkeypatch.setenv("XDG_DATA_HOME", value)

    assert _user_data_dir("App") == home / ".local" / "share" / "App"


@pytest.mark.parametrize("system", ("win32", "darwin", "linux"))
def test_the_name_is_the_last_part_on_every_platform(on, home, system):
    on(system)

    assert _user_data_dir("App").name == "App"


@pytest.mark.parametrize("system", ("win32", "darwin", "linux"))
def test_nothing_is_created_by_asking(on, home, system, tmp_path, monkeypatch):
    def refuse(self, mode=0o777, parents=False, exist_ok=False):
        raise AssertionError(f"created {self}")

    on(system)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "share"))
    monkeypatch.setattr(Path, "mkdir", refuse)

    assert not _user_data_dir("App").exists()


@pytest.mark.parametrize("value", BLANK)
def test_the_answer_is_absolute_however_blank_the_variables_are(home,
                                                                monkeypatch,
                                                                value):
    # The branch of the running machine, because is_absolute() answers for
    # the flavour of path it was built with: '/srv/data' is not absolute to
    # a WindowsPath. The router resolves whatever it is given, so a relative
    # default would land beside wherever the process was started.
    monkeypatch.setenv("LOCALAPPDATA", value)
    monkeypatch.setenv("XDG_DATA_HOME", value)

    assert _user_data_dir("App").is_absolute()


def test_the_module_constants_are_the_function_applied_to_the_name():
    assert DATA_DIR == _user_data_dir(NAME)
    assert UPLOADS_DIR == DATA_DIR / "uploads"
    assert NAME == "FuncToWeb"


@pytest.mark.skipif(sys.platform != "win32", reason="the branch of this machine")
def test_the_real_windows_answer_is_under_local_appdata():
    assert DATA_DIR.parent.name == "Local"
    assert DATA_DIR.parent.parent.name == "AppData"


def test_it_agrees_with_platformdirs_on_this_platform():
    """The dependency this replaced, kept as the oracle while it is around.

    It is not a dependency of the package or of its tests any more, so this
    skips itself where it is absent. Where it is present it states the point
    of the whole change: the same path, without the library.
    """
    platformdirs = pytest.importorskip("platformdirs")

    theirs = platformdirs.user_data_path(NAME, appauthor=False)

    assert DATA_DIR == theirs
