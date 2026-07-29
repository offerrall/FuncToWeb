from os import environ
from pathlib import Path
from tempfile import gettempdir

from platformdirs import user_data_path

__version__ = "2.0.0"

NAME: str = "".join(part.title() for part in __name__.split(".")[0].split("_"))
DATA_DIR: Path = user_data_path(NAME, appauthor=False)
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
