from pathlib import Path

NAME_LIMIT: int = 255

TOKEN_DIGITS: int = 32

PARTIAL_SUFFIX: int = len(".") + TOKEN_DIGITS + len(".part")

IDENTIFIER_PREFIX: int = TOKEN_DIGITS + len(".")

PENDING_MARKER: str = "~p"

RETURNS_MARKER: str = "~r"

RESERVED_MARKERS: tuple[str, ...] = (PENDING_MARKER, RETURNS_MARKER)

STAMP_DIGITS: int = 10

STAMP_CLOSE: str = "~"

PENDING_PREFIX: int = len(PENDING_MARKER) + STAMP_DIGITS + len(STAMP_CLOSE)

RETURNS_PREFIX: int = len(RETURNS_MARKER) + STAMP_DIGITS + len(STAMP_CLOSE)

REFERENCE_LIMIT: int = NAME_LIMIT - PARTIAL_SUFFIX - PENDING_PREFIX

RETURN_LIMIT: int = NAME_LIMIT - PARTIAL_SUFFIX

FILENAME_LIMIT: int = RETURN_LIMIT - IDENTIFIER_PREFIX - RETURNS_PREFIX

RESERVED_NAMES: frozenset[str] = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + [f"COM{digit}" for digit in range(1, 10)]
    + [f"LPT{digit}" for digit in range(1, 10)]
)

FORBIDDEN_CHARACTERS: frozenset[str] = frozenset('<>:"|?*')


def segment_of(reference: str | None, limit: int = REFERENCE_LIMIT) -> str:
    if type(reference) is not str or not reference or reference in (".", ".."):
        raise ValueError("must be a file name")

    if "/" in reference or "\\" in reference:
        raise ValueError("cannot contain separators")

    if any(character < " " for character in reference):
        raise ValueError("cannot contain a control character")

    if FORBIDDEN_CHARACTERS.intersection(reference):
        raise ValueError('cannot contain any of <>:"|?*')

    _refuse_reserved(reference)

    if reference.strip(".") == "":
        raise ValueError("must be a file name")

    if reference[-1] in ". ":
        raise ValueError("cannot end with a dot or a space")

    if reference.split(".")[0].upper() in RESERVED_NAMES:
        raise ValueError("is a reserved device name")

    if len(reference.encode("utf-8")) > limit:
        raise ValueError(f"is longer than {limit} bytes")

    path = Path(reference)

    if path.is_absolute() or path.name != reference:
        raise ValueError("must be a file name")

    return reference


def stored_of(reference: str, root: Path) -> Path:
    if type(reference) is not str or not reference:
        raise ValueError("must be a file name")

    base = root.resolve()

    if ("/" in reference or "\\" in reference
            or FORBIDDEN_CHARACTERS.intersection(reference)
            or Path(reference).name != reference):
        raise ValueError("is not a file of the storage directory")

    try:
        candidate = (root / reference).resolve()
    except OSError as error:
        raise ValueError("is not a usable path") from error

    if candidate.parent != base:
        raise ValueError("is not a file of the storage directory")

    _refuse_reserved(candidate.name)

    return candidate


def _refuse_reserved(name: str) -> None:
    for marker in RESERVED_MARKERS:
        if name.startswith(marker):
            raise ValueError(
                f"cannot start with the reserved prefix '{marker}'"
            )
