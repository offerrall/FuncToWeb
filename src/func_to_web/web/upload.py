import os
from collections.abc import Awaitable, Callable
from datetime import timedelta
from pathlib import Path
from random import uniform
from threading import Lock, Thread
from time import sleep
from uuid import uuid4
from warnings import warn

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from func_to_web.config import UPLOADS_DIR as UPLOADS_DIR
from func_to_web.web import pending, returned_files
from func_to_web.web.pending import DEFAULT_TTL as DEFAULT_TTL
from func_to_web.web.pending import (
    discard,
    now,
    pending_of,
    stamps_of,
    taken,
)
from func_to_web.web.references import PENDING_MARKER, segment_of, stored_of

TOO_LARGE: int = 413

CONFLICT: int = 409

ALREADY_STORED: str = "a file with this reference already exists"

PUBLISH_ATTEMPTS: int = 5

PUBLISH_PAUSE: float = 0.01

SWEEP_MIN_SECONDS: float = 30 * 60

SWEEP_MAX_SECONDS: float = 60 * 60

SWEEPER_NAME: str = "func-to-web-storage-sweeper"

# The sweeper is one per process, not one per router and not one per
# directory: several spaces mounted together must not each start a thread.
# The first router with file fields fixes the directory and the TTL of the
# whole process, for the thread and for the resolver.
_state: Lock = Lock()

_ttl: int | None = DEFAULT_TTL

_adopted: bool = False

_sweeper: Thread | None = None


def target_of(reference: str | None) -> Path:
    return UPLOADS_DIR / segment_of(reference)


def published_of(reference: str) -> Path:
    """Where /upload lands: a pending name, or the bare one with no TTL."""
    if _ttl is None:
        return UPLOADS_DIR / reference

    return UPLOADS_DIR / pending_of(reference, now())


def stored_file(reference: str) -> str:
    """The local path of a reference, promoting it if it is still pending.

    The path that comes out is always the bare one, so the prefix never
    escapes this function: what the caller stores stays stable.
    """
    try:
        target = stored_of(reference, UPLOADS_DIR)
    except ValueError as error:
        raise ValueError(
            f"invalid file reference {reference!r}: {error}"
        ) from error

    for remaining in reversed(range(PUBLISH_ATTEMPTS)):
        if target.is_file():
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
    only when resolving it under UPLOADS_DIR lands back on the very file it
    was given. That is what keeps a symbolic link honest in both directions —
    one pointing at another stored file keeps its own name instead of being
    silently renamed to its target, and one pointing outside is refused here
    rather than emitted as a reference the resolver would then reject.
    """
    try:
        candidate = Path(path).resolve()
        name = Path(path).name
        round_trip = (UPLOADS_DIR / name).resolve()
    except (OSError, ValueError):
        return None

    if candidate.parent != UPLOADS_DIR.resolve() or round_trip != candidate:
        return None

    if (name.startswith(PENDING_MARKER)
            or candidate.name.startswith(PENDING_MARKER)):
        return None

    return name


def _pending_source(reference: str) -> Path | None:
    """The oldest live pending file, discarding the expired ones on the way."""
    for stamp in stamps_of(UPLOADS_DIR, reference):
        source = UPLOADS_DIR / pending_of(reference, stamp)

        if _ttl is not None and now() - stamp >= _ttl:
            discard(source)

            continue

        return source

    return None


def sweep() -> None:
    """One sweep of the storage directory with the effective TTL."""
    if _ttl is None:
        return

    pending.sweep(UPLOADS_DIR, _ttl)


def start_pending(directory: Path, ttl: int | None) -> None:
    """Adopt the uploads storage, sweep now and start the sweeper if needed.

    One process is one storage directory, so where the files go and how long
    they last are settled together by the first router that gets here, and a
    later one asking for either differently is told that it was not applied.
    The sweep is synchronous as well as threaded because a short-lived
    process may exit before the thread wakes.
    """
    global UPLOADS_DIR, _ttl, _adopted

    with _state:
        if not _adopted:
            UPLOADS_DIR = directory
            _ttl = ttl
            _adopted = True

        settled_directory = UPLOADS_DIR
        settled_ttl = _ttl

        _start_sweeper(settled_ttl is not None)

    if directory != settled_directory:
        _ignored("uploads_dir", directory, settled_directory)

    if ttl != settled_ttl:
        _ignored("pending_ttl", ttl, settled_ttl)

    sweep()


def start_returns(directory: Path, ttl: int | None) -> None:
    """Adopt the returns storage, sweep now and start the sweeper if needed.

    A separate decision under the same policy: two directories, two TTLs and
    one thread, which is why both routes settle theirs through here.
    """
    settled_directory, settled_ttl = returned_files.adopt(directory, ttl)

    with _state:
        _start_sweeper(settled_ttl is not None)

    if directory != settled_directory:
        _ignored("returns_dir", directory, settled_directory)

    if ttl != settled_ttl:
        _ignored("returns_ttl", ttl, settled_ttl)

    returned_files.sweep()


def _start_sweeper(needed: bool) -> None:
    global _sweeper

    if needed and _sweeper is None:
        _sweeper = Thread(target=_sweeping, name=SWEEPER_NAME, daemon=True)
        _sweeper.start()


def _ignored(name: str, asked: object, settled: object) -> None:
    """Say that a setting arrived after the process had already settled it.

    One piece of prose for every storage setting: only the name and the two
    values change, so whatever else becomes a policy of the process reads the
    same way here.
    """
    warn(
        f"{name}={asked!r} is ignored: this process already stores its files "
        f"with {name}={settled!r}, settled by an earlier router. Storage is "
        f"one policy per process, not one per router.",
        stacklevel=4,
    )


def _sweeping() -> None:
    while True:
        for directory_sweep in (sweep, returned_files.sweep):
            try:
                directory_sweep()
            except Exception:
                # A failed pass is never the end of the thread: whatever it
                # was, the next cycle finds the same directory and tries
                # again.
                continue

        # Drawn again every cycle: workers that started together must drift
        # apart instead of sweeping in lockstep forever.
        sleep(uniform(SWEEP_MIN_SECONDS, SWEEP_MAX_SECONDS))


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

        if taken(UPLOADS_DIR, reference):
            raise HTTPException(CONFLICT, ALREADY_STORED)

        if max_upload_bytes is not None:
            _refuse_declared(request, max_upload_bytes)

        partial = target.with_name(f"{reference}.{uuid4().hex}.part")

        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

        published = False

        try:
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

            _publish(partial, published_of(reference))

            published = True
        finally:
            if not published:
                try:
                    partial.unlink(missing_ok=True)
                except OSError:
                    pass

        return JSONResponse({"uploaded": True})

    return upload


def _publish(partial: Path, target: Path) -> None:
    for remaining in reversed(range(PUBLISH_ATTEMPTS)):
        try:
            os.replace(partial, target)
            return
        except OSError:
            if not remaining:
                raise

            sleep(PUBLISH_PAUSE)


def _too_large(limit: int) -> str:
    return f"uploaded file exceeds the maximum size of {limit} bytes"


def _refuse_declared(request: Request, limit: int) -> None:
    declared = request.headers.get("content-length")

    if declared is not None and declared.isdigit() and int(declared) > limit:
        raise HTTPException(TOO_LARGE, _too_large(limit))
