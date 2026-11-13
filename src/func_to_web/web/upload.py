import errno
import os
from collections.abc import Awaitable, Callable
from datetime import timedelta
from pathlib import Path
from time import sleep

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from func_to_web.web.pending import (
    discard,
    now,
    pending_of,
    stamps_of,
    taken,
)
from func_to_web.web.references import PENDING_MARKER, segment_of, stored_of
from func_to_web.web.storage import (
    PUBLISH_ATTEMPTS,
    PUBLISH_PAUSE,
    UPLOADS,
    partial_in,
    publish,
)

TOO_LARGE: int = 413

CONFLICT: int = 409

ALREADY_STORED: str = "a file with this reference already exists"


def target_of(reference: str | None) -> Path:
    return UPLOADS.directory / segment_of(reference)


def published_of(reference: str) -> Path:
    """Where /upload lands: a pending name, or the bare one with no TTL."""
    if UPLOADS.ttl is None:
        return UPLOADS.directory / reference

    return UPLOADS.directory / pending_of(reference, now())


def stored_file(reference: str) -> str:
    """The local path of a reference, promoting it if it is still pending.

    The path that comes out is always the bare one, so the prefix never
    escapes this function: what the caller stores stays stable.
    """
    try:
        target = stored_of(reference, UPLOADS.directory)
    except ValueError as error:
        raise ValueError(
            f"invalid file reference {reference!r}: {error}"
        ) from error

    for remaining in reversed(range(PUBLISH_ATTEMPTS)):
        try:
            exists = target.is_file()
        except OSError as error:
            # resolve() may accept a name that stat() cannot address. Refuse
            # that input without masking unrelated storage failures.
            if error.errno != errno.ENAMETOOLONG:
                raise
            raise ValueError("file reference is too long") from error

        if exists:
            return str(target)

        source = _pending_source(target.name)

        if source is None:
            break

        try:
            os.replace(source, target)

            return str(target)
        except OSError:
            # The pending file is gone: another execution promoted it while we
            # were looking, so the bare name is already there. Same short
            # retry as publishing, which covers Windows renaming at once too.
            if not remaining:
                break

            sleep(PUBLISH_PAUSE)

    raise FileNotFoundError(f"File not found: {reference}")


def reference_of(path: str) -> str | None:
    """The reference of a stored path, or None if storage does not own it.

    The inverse of stored_file(), and it checks itself: the name is emitted
    only when resolving it under the uploads directory lands back on the very
    file it was given. That is what keeps a symbolic link honest in both
    directions — one pointing at another stored file keeps its own name
    instead of being silently renamed to its target, and one pointing outside
    is refused here rather than emitted as a reference the resolver would
    then reject.
    """
    try:
        candidate = Path(path).resolve()
        name = Path(path).name
        round_trip = (UPLOADS.directory / name).resolve()
    except (OSError, ValueError):
        return None

    if (candidate.parent != UPLOADS.directory.resolve()
            or round_trip != candidate):
        return None

    if (name.startswith(PENDING_MARKER)
            or candidate.name.startswith(PENDING_MARKER)):
        return None

    return name


def _pending_source(reference: str) -> Path | None:
    """The oldest live pending file, discarding the expired ones on the way."""
    ttl = UPLOADS.ttl

    for stamp in stamps_of(UPLOADS.directory, reference):
        source = UPLOADS.directory / pending_of(reference, stamp)

        if ttl is not None and now() - stamp >= ttl:
            discard(source)

            continue

        return source

    return None


def checked_limit(value: int | None) -> int | None:
    if value is None:
        return None

    if type(value) is not int:
        raise TypeError("max_upload_bytes must be int or None")

    if value <= 0:
        raise ValueError("max_upload_bytes must be greater than zero")

    return value


def checked_ttl(value: int | timedelta | None, name: str) -> int | None:
    if value is None:
        return None

    if isinstance(value, timedelta):
        seconds = int(value.total_seconds())
    elif type(value) is int:
        seconds = value
    else:
        raise TypeError(f"{name} must be int, timedelta or None")

    if seconds <= 0:
        raise ValueError(f"{name} must be greater than zero")

    return seconds


def uploader(
    max_upload_bytes: int | None,
) -> Callable[[Request], Awaitable[JSONResponse]]:
    async def upload(request: Request) -> JSONResponse:
        try:
            target = target_of(request.headers.get("X-File-Reference"))
        except ValueError as error:
            raise HTTPException(400, f"X-File-Reference {error}") from error

        reference = target.name

        if taken(UPLOADS.directory, reference):
            raise HTTPException(CONFLICT, ALREADY_STORED)

        if max_upload_bytes is not None:
            _refuse_declared(request, max_upload_bytes)

        with partial_in(UPLOADS.directory, reference) as partial:
            with partial.open("xb") as file:
                received = 0

                async for chunk in request.stream():
                    if not chunk:
                        continue

                    received += len(chunk)

                    if (max_upload_bytes is not None
                            and received > max_upload_bytes):
                        raise HTTPException(TOO_LARGE,
                                            _too_large(max_upload_bytes))

                    file.write(chunk)

            publish(partial, published_of(reference))

        return JSONResponse({"uploaded": True})

    return upload


def _too_large(limit: int) -> str:
    return f"uploaded file exceeds the maximum size of {limit} bytes"


def _refuse_declared(request: Request, limit: int) -> None:
    declared = request.headers.get("content-length")

    if declared is not None and declared.isdigit() and int(declared) > limit:
        raise HTTPException(TOO_LARGE, _too_large(limit))
