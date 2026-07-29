import os
from pathlib import Path
from shutil import copyfile
from threading import Lock
from uuid import uuid4

from func_to_web.config import RETURNS_DIR as RETURNS_DIR
from func_to_web.web import pending
from func_to_web.web.pending import (
    DEFAULT_TTL,
    now,
    returned_of,
    stamped_of,
)
from func_to_web.web.references import (
    RETURN_LIMIT,
    RETURNS_MARKER,
    segment_of,
    stored_of,
)

_state: Lock = Lock()

_ttl: int | None = DEFAULT_TTL

_adopted: bool = False


def store(source: Path | bytes, filename: str) -> str:
    reference = f"{uuid4().hex}.{_dated(filename)}"
    target = RETURNS_DIR / reference
    partial = target.with_name(f"{target.name}.{uuid4().hex}.part")

    RETURNS_DIR.mkdir(parents=True, exist_ok=True)

    published = False

    try:
        if isinstance(source, bytes):
            partial.write_bytes(source)
        else:
            copyfile(_readable(source), partial)

        os.replace(partial, target)
        published = True
    finally:
        if not published:
            partial.unlink(missing_ok=True)

    return reference


def stored_return(reference: str) -> tuple[Path, str]:
    target = stored_of(segment_of(reference, RETURN_LIMIT), RETURNS_DIR)

    if not target.is_file():
        raise FileNotFoundError(f"File not found: {reference}")

    return target, _public_name(reference)


def adopt(directory: Path, ttl: int | None) -> tuple[Path, int | None]:
    """Settle the returns storage and report the directory and TTL in force.

    One process is one returns directory, so it is one policy, exactly as
    with the uploads one: the first router that gets here decides for every
    space mounted afterwards, and it decides both halves at once.
    """
    global RETURNS_DIR, _ttl, _adopted

    with _state:
        if not _adopted:
            RETURNS_DIR = directory
            _ttl = ttl
            _adopted = True

        return RETURNS_DIR, _ttl


def sweep() -> None:
    """One sweep of the returns directory with the effective TTL."""
    if _ttl is None:
        return

    pending.sweep_returns(RETURNS_DIR, _ttl)


def _dated(filename: str) -> str:
    """The public name with the moment it is published in front of it.

    The date travels in the name and not in the mtime because a copy, a
    backup or an antivirus rewrites the mtime of a file nobody asked about.
    """
    if _ttl is None:
        return filename

    return stamped_of(filename, now(), RETURNS_MARKER)


def _readable(source: Path) -> Path:
    if not source.exists():
        raise FileNotFoundError(f"File not found: {source.name}")

    if not source.is_file():
        raise IsADirectoryError(f"Not a file: {source.name}")

    return source


def _public_name(reference: str) -> str:
    found = returned_of(reference)

    if found is not None:
        return found[1]

    _, _, name = reference.partition(".")

    return name or reference
