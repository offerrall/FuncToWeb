"""Life cycle of the files the library publishes with a date in their name.

/upload publishes under a pending name that carries the moment the bytes
landed; the first successful resolution renames it to the bare reference and
from then on it is permanent. What is never resolved expires. A returned file
carries its date behind the identifier and expires without ever being
promoted: nothing consumes a download, so nothing makes it permanent.

```text
~p<10 digits>~<reference>              pending, deleted once it expires
<reference>                            promoted, never touched again
<32 hex>.~r<10 digits>~<public name>   returned, deleted once it expires
```

Every function here takes the storage directory as an argument: the module
knows the naming rules, not where the files live.
"""

import os
from pathlib import Path
from time import time

from func_to_web.web.references import (
    PENDING_MARKER,
    RETURNS_MARKER,
    STAMP_CLOSE,
    STAMP_DIGITS,
    TOKEN_DIGITS,
)

DEFAULT_TTL: int = 60 * 60

PART_SUFFIX: str = ".part"

HEX_DIGITS: frozenset[str] = frozenset("0123456789abcdef")


def now() -> int:
    return int(time())


def stamped_of(reference: str, stamp: int, marker: str) -> str:
    """The name a reference published at that second takes under a marker."""
    return f"{marker}{stamp:0{STAMP_DIGITS}d}{STAMP_CLOSE}{reference}"


def pending_of(reference: str, stamp: int) -> str:
    """The pending name of a reference published at that second."""
    return stamped_of(reference, stamp, PENDING_MARKER)


def parsed(name: str, marker: str = PENDING_MARKER) -> tuple[int, str] | None:
    """(stamp, reference) of a dated name, or None if it is not one.

    Read by hand, never with glob(): a legal reference can contain [ or ],
    which any pattern would take as a character class.
    """
    if not name.startswith(marker):
        return None

    body = name[len(marker):]
    stamp = body[:STAMP_DIGITS]
    closing = body[STAMP_DIGITS:STAMP_DIGITS + len(STAMP_CLOSE)]
    reference = body[STAMP_DIGITS + len(STAMP_CLOSE):]

    if closing != STAMP_CLOSE or not reference:
        return None

    if len(stamp) != STAMP_DIGITS or not (stamp.isascii() and stamp.isdigit()):
        return None

    return int(stamp), reference


def returned_of(name: str) -> tuple[int, str] | None:
    """(stamp, public name) of a returned file, or None if it is not one.

    The identifier is read as strictly as the date, and both must be there:
    the returns directory lives in the system temporary directory, among
    files nobody here wrote, and a name that does not parse is one of those.
    """
    token, dot, dated = name.partition(".")

    if not dot or not _is_token(token):
        return None

    return parsed(dated, RETURNS_MARKER)


def is_partial(name: str) -> bool:
    """Whether a name is a partial file of the publishing dance.

    Read strictly —the token is exactly the 32 hex digits of a uuid4— because
    the sweep decides on this branch by mtime alone: the suffix on its own
    would reach a promoted reference that merely ends in .part, deleting a
    file that is meant to be permanent and freeing its name to be written
    again. The residue is a reference shaped exactly like a partial,
    `x.<32 hex>.part`, a window narrow enough to accept.
    """
    if not name.endswith(PART_SUFFIX):
        return False

    body = name[:-len(PART_SUFFIX)]

    if len(body) <= TOKEN_DIGITS + 1 or body[-TOKEN_DIGITS - 1] != ".":
        return False

    return _is_token(body[-TOKEN_DIGITS:])


def names_of(root: Path) -> list[str]:
    try:
        return os.listdir(root)
    except OSError:
        return []


def taken(root: Path, reference: str) -> bool:
    """A reference exists as the bare name or as a pending one, any date."""
    for name in names_of(root):
        if name == reference:
            return True

        found = parsed(name)

        if found is not None and found[1] == reference:
            return True

    return False


def stamps_of(root: Path, reference: str) -> list[int]:
    """Every pending stamp of a reference, oldest first.

    Ascending, so whoever reads it takes the oldest that suits them: two
    simultaneous first uploads both publish, and the first one is the one the
    409 would have kept.
    """
    return sorted(
        found[0]
        for name in names_of(root)
        if (found := parsed(name)) is not None and found[1] == reference
    )


def discard(path: Path) -> None:
    """Delete without ever raising: losing the race is the normal outcome."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def sweep(root: Path, ttl: int) -> None:
    """One pass: expired pending files, malformed ones and stale partials.

    Bare names are never touched, and neither are live pending files or fresh
    partials. Both branches read the name the way the server writes it —the
    marker parsed whole, the partial token counted— so a promoted reference
    is safe whatever it is called. A name that carries the marker but does
    not parse is rubbish by definition: the server never writes one.
    """
    moment = now()

    for name in names_of(root):
        try:
            if name.startswith(PENDING_MARKER):
                found = parsed(name)

                if found is None or moment - found[0] >= ttl:
                    discard(root / name)
            elif is_partial(name) and _stale(root / name, moment, ttl):
                discard(root / name)
        except Exception:
            # One unreadable entry is not worth the rest of the pass, nor the
            # thread: whatever it was, the next cycle sees it again.
            continue


def sweep_returns(root: Path, ttl: int) -> None:
    """One pass over a directory the library does not have to itself.

    Here the rule is the other way round from the pending one: only what
    parses whole is deleted, and everything else stays. Somebody else's file
    and a return stored before the date existed look the same from here, and
    neither is ours to remove.
    """
    moment = now()

    for name in names_of(root):
        try:
            found = returned_of(name)

            if found is None:
                if is_partial(name) and _stale(root / name, moment, ttl):
                    discard(root / name)
            elif moment - found[0] >= ttl:
                discard(root / name)
        except Exception:
            continue


def _is_token(text: str) -> bool:
    return (len(text) == TOKEN_DIGITS
            and all(character in HEX_DIGITS for character in text))


def _stale(path: Path, moment: int, ttl: int) -> bool:
    """A partial file carries no date in its name, so here mtime decides."""
    try:
        return moment - int(path.stat().st_mtime) >= ttl
    except OSError:
        return False
