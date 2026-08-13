from os import environ
from pathlib import Path
from sys import platform
from tempfile import gettempdir

__version__ = "2.6.0"

NAME: str = "".join(part.title() for part in __name__.split(".")[0].split("_"))


def _user_data_dir(name: str) -> Path:
    """Where this platform keeps the data of an application, `name` inside.

    The three conventions, each read from the machine that answers for it:
    `%LOCALAPPDATA%` on Windows, `Application Support` on macOS and the XDG
    spec everywhere else. Windows sets that variable at login from the same
    known folder the shell API returns, so the two are one source of truth
    read by two roads; the home directory covers a process that was handed
    an environment without it.

    Nothing is created here. The directory is made when a router settles it,
    which is also where a location this process cannot write to is refused.
    """
    base: str | Path

    if platform == "win32":
        base = _asked("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
    elif platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = _asked("XDG_DATA_HOME") or Path.home() / ".local" / "share"

    return Path(base) / name


def _asked(variable: str) -> str:
    """The variable, or nothing when it is unset or holds only blanks.

    A variable exported empty is what a shell leaves behind when it means
    nothing, and joining it would hand back a path relative to wherever the
    process was started —which the XDG spec says to ignore, and which no
    caller of this would ever want.
    """
    value = environ.get(variable, "")

    return value if value.strip() else ""


DATA_DIR: Path = _user_data_dir(NAME)
UPLOADS_DIR: Path = DATA_DIR / "uploads"

RETURNS_DIR: Path = Path(gettempdir()) / NAME / "returns"

UPLOADS_VARIABLE: str = "FUNCTOWEB_UPLOADS_DIR"

RETURNS_VARIABLE: str = "FUNCTOWEB_RETURNS_DIR"


def checked_uploads_dir(value: str | Path | None) -> Path:
    """The uploads directory a router asks for, ready to be written to."""
    return _checked(value, "uploads_dir", UPLOADS_VARIABLE, UPLOADS_DIR)


def checked_returns_dir(value: str | Path | None) -> Path:
    """The returns directory a router asks for, ready to be written to."""
    return _checked(value, "returns_dir", RETURNS_VARIABLE, RETURNS_DIR)


def _checked(value: str | Path | None, name: str, variable: str,
             default: Path) -> Path:
    """The argument, the environment variable or the default, in that order.

    Whichever of the three wins is made absolute and created here, so a
    location this process cannot store files in is a failure of the build and
    never of the first request. The environment variable is read now and not
    when the module loads, because what settles the directory is building a
    router.
    """
    if value is None:
        asked = environ.get(variable)
        chosen: str | Path = default if asked is None else asked
    elif isinstance(value, (str, Path)):
        chosen = value
    else:
        raise TypeError(f"{name} must be str, Path or None")

    directory = Path(chosen).resolve()

    if directory.exists() and not directory.is_dir():
        raise ValueError(f"{name} is not a directory: {directory}")

    directory.mkdir(parents=True, exist_ok=True)

    return directory
