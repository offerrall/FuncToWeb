import os

from func_to_web.web import returned_files, upload


def without_storage_paths(text: str) -> str:
    """The same message with the storage directories cut out of any path.

    A certification message names the file the core inspected, and what the
    core inspected is the path the resolver returned, so this is the one place
    a local path would still reach the client. Only the directory goes: what
    is left is the file name, which is the reference the client already sent.

    The core writes the path with !r, so it also travels with its separators
    doubled; both renderings are cut, and the comparison folds case because
    Windows does.
    """
    for root in (upload.UPLOADS_DIR, returned_files.RETURNS_DIR):
        for prefix in _prefixes(str(root)):
            text = _cut(text, prefix)

    return text


def _prefixes(root: str) -> tuple[str, ...]:
    plain = root + os.sep
    escaped = repr(root)[1:-1] + repr(os.sep)[1:-1]

    return (escaped, plain) if escaped != plain else (plain,)


def _cut(text: str, prefix: str) -> str:
    folded = os.path.normcase(text)
    target = os.path.normcase(prefix)

    # normcase lowercases, and a handful of characters change length when they
    # do; the folded index would then point somewhere else in the original.
    if len(folded) != len(text) or len(target) != len(prefix):
        return text.replace(prefix, "")

    pieces = []
    index = 0

    while True:
        found = folded.find(target, index)

        if found < 0:
            pieces.append(text[index:])

            return "".join(pieces)

        pieces.append(text[index:found])
        index = found + len(target)
