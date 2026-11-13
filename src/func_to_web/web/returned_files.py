from pathlib import Path
from shutil import copyfile
from uuid import uuid4

from func_to_web.web.pending import now, returned_of, stamped_of
from func_to_web.web.references import (
    RETURN_LIMIT,
    RETURNS_MARKER,
    segment_of,
    stored_of,
)
from func_to_web.web.storage import RETURNS, partial_in, publish


def store(source: Path | bytes, filename: str) -> str:
    reference = f"{uuid4().hex}.{_dated(filename)}"

    with partial_in(RETURNS.directory, reference) as partial:
        if isinstance(source, bytes):
            partial.write_bytes(source)
        else:
            copyfile(_readable(source), partial)

        publish(partial, RETURNS.directory / reference)

    return reference


def stored_return(reference: str) -> tuple[Path, str]:
    target = stored_of(segment_of(reference, RETURN_LIMIT),
                       RETURNS.directory)

    if not target.is_file():
        raise FileNotFoundError(f"File not found: {reference}")

    return target, _public_name(reference)


def _dated(filename: str) -> str:
    """The public name with the moment it is published in front of it.

    The date travels in the name and not in the mtime because a copy, a
    backup or an antivirus rewrites the mtime of a file nobody asked about.
    """
    if RETURNS.ttl is None:
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
