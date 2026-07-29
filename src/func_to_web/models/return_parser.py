from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import NoneType, UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from func_to_web.web.references import FILENAME_LIMIT, segment_of

if TYPE_CHECKING:
    from func_to_web.models.function import WebFunction


class ReturnContractError(TypeError):
    """Raised when a return breaks the contract it declared.

    Both the annotation FuncToWeb compiles and the value the function
    returned for it can raise it.
    """


@dataclass(frozen=True)
class Download:
    """Return annotation mark: what it wraps is offered as a file.

    The marked Path, str or bytes is stored and downloaded instead of being
    rendered. filename may be a fixed str, a callable (value, index) -> str,
    or None to take the name from the returned path; anything else raises
    TypeError.
    """

    filename: str | Callable[[object, int], str] | None = None

    def __post_init__(self) -> None:
        if self.filename is None or isinstance(self.filename, str):
            return

        if not callable(self.filename):
            raise TypeError(
                f"Download.filename must be str, a callable or None, got "
                f"{type(self.filename).__name__}"
            )


@dataclass(frozen=True)
class OpenForm:
    """Return annotation mark: the result opens another form prefilled.

    target must be a function or WebFunction registered in the same space,
    and hidden names the parameters that opening does not show. Raises
    TypeError for an invalid target or hidden tuple.
    """

    target: "Callable[..., Any] | WebFunction"
    hidden: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        from func_to_web.models.function import WebFunction

        if not callable(self.target) and type(self.target) is not WebFunction:
            raise TypeError(
                f"OpenForm.target must be a function or a WebFunction, got "
                f"{type(self.target).__name__}"
            )

        if type(self.hidden) is not tuple:
            raise TypeError(
                f"OpenForm.hidden must be a tuple, got "
                f"{type(self.hidden).__name__}"
            )

        if any(type(name) is not str for name in self.hidden):
            raise TypeError("OpenForm.hidden must contain only str")


_UNIONS = (Union, UnionType)

_FILE_TYPES: tuple[type, ...] = (Path, str, bytes)


@dataclass(frozen=True)
class _Value:
    types: tuple[type, ...]


@dataclass(frozen=True)
class _Sequence:
    item: "_Shape"


@dataclass(frozen=True)
class _Positional:
    items: tuple["_Shape", ...]


_Shape = _Value | _Sequence | _Positional


@dataclass(frozen=True)
class _Group:
    mark: Download
    shape: _Shape


@dataclass(frozen=True)
class _Optional:
    node: "_Node"


@dataclass(frozen=True)
class _Each:
    item: "_Node"


@dataclass(frozen=True)
class _Items:
    items: tuple["_Node | None", ...]


_Node = _Group | _Optional | _Each | _Items


@dataclass(frozen=True)
class _ReturnedFile:
    source: Path | bytes
    filename: str


@dataclass(frozen=True)
class ReturnParser:
    """What a return annotation declared, compiled once.

    form carries the OpenForm that marks the whole return, or None; root is
    the compiled shape of its Download marks, and is None when the return
    declares none — read it only as a presence check, because its node types
    are internal. resolved() applies the contract to a returned value and
    raises ReturnContractError when it does not hold.
    """

    root: "_Node | None"
    form: OpenForm | None = None

    def resolved(self, returned: Any) -> Any:
        return returned if self.root is None else _resolve(self.root, returned)


def parser_of(fn: Callable[..., Any]) -> ReturnParser | None:
    annotation = get_type_hints(fn, include_extras=True).get("return")

    if annotation is None:
        return None

    form, inner = _root_form(annotation)

    if _forms_in(annotation) > (0 if form is None else 1):
        raise ReturnContractError(
            "OpenForm can only mark the whole return, and only once"
        )

    root = _compile(inner)

    if form is not None and root is not None:
        raise ReturnContractError(
            "a return cannot mix OpenForm and Download"
        )

    if form is None and root is None:
        return None

    return ReturnParser(root, form)


def _root_form(annotation: Any) -> tuple[OpenForm | None, Any]:
    if get_origin(annotation) is not Annotated:
        return None, annotation

    args = get_args(annotation)
    marks = [item for item in args[1:] if type(item) is OpenForm]

    if not marks:
        return None, annotation

    if len(marks) > 1:
        raise ReturnContractError(
            "an Annotated cannot carry more than one OpenForm"
        )

    if any(type(item) is Download for item in args[1:]):
        raise ReturnContractError("a return cannot mix OpenForm and Download")

    return marks[0], args[0]


def _forms_in(annotation: Any) -> int:
    if get_origin(annotation) is Annotated:
        args = get_args(annotation)
        here = sum(1 for item in args[1:] if type(item) is OpenForm)

        return here + _forms_in(args[0])

    return sum(_forms_in(option) for option in get_args(annotation))


def _names_of(types: tuple[type, ...]) -> str:
    return " or ".join(item.__name__ for item in types)


def _name_of(value: Any) -> str:
    return "Path" if isinstance(value, Path) else type(value).__name__


def _mark_of(metadata: tuple[Any, ...]) -> Download | None:
    marks = [item for item in metadata if type(item) is Download]

    if len(marks) > 1:
        raise ReturnContractError(
            "an Annotated cannot carry more than one Download"
        )

    return marks[0] if marks else None


def _variadic(args: tuple[Any, ...]) -> bool:
    return len(args) == 2 and args[1] is Ellipsis


def _compile(annotation: Any) -> "_Node | None":
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Annotated:
        mark = _mark_of(args[1:])

        if mark is None:
            return _compile(args[0])

        return _Group(mark, _shape(args[0]))

    if origin in _UNIONS:
        return _compile_union(args)

    if origin is list:
        item = _compile(args[0]) if args else None

        return None if item is None else _Each(item)

    if origin is tuple:
        return _compile_tuple(args)

    return None


def _compile_union(args: tuple[Any, ...]) -> "_Node | None":
    optional = any(option is NoneType for option in args)

    nodes: list[_Node] = []
    ordinary = False

    for option in args:
        if option is NoneType:
            continue

        node = _compile(option)

        if node is None:
            ordinary = True
        else:
            nodes.append(node)

    if not nodes:
        return None

    if ordinary:
        raise ReturnContractError(
            "a union cannot mix Download and ordinary return branches"
        )

    if len(nodes) > 1:
        raise ReturnContractError(
            "a union cannot carry more than one Download branch"
        )

    return _Optional(nodes[0]) if optional else nodes[0]


def _compile_tuple(args: tuple[Any, ...]) -> "_Node | None":
    if not args or args == ((),):
        return None

    if _variadic(args):
        item = _compile(args[0])

        return None if item is None else _Each(item)

    nodes = tuple(_compile(option) for option in args)

    if all(node is None for node in nodes):
        return None

    return _Items(nodes)


def _shape(annotation: Any) -> _Shape:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Annotated:
        if _mark_of(args[1:]) is not None:
            raise ReturnContractError(
                "a Download cannot contain another Download"
            )

        return _shape(args[0])

    if origin in _UNIONS:
        return _shape_union(args)

    if origin is list:
        return _Sequence(_shape(args[0]) if args else _Value(_FILE_TYPES))

    if origin is tuple:
        if not args or args == ((),):
            return _Sequence(_Value(_FILE_TYPES))

        if _variadic(args):
            return _Sequence(_shape(args[0]))

        return _Positional(tuple(_shape(option) for option in args))

    if annotation in _FILE_TYPES:
        return _Value((annotation,))

    if annotation is NoneType:
        raise ReturnContractError(
            "None is not allowed inside a Download; it can replace a whole "
            "Download return, not one of its files"
        )

    raise ReturnContractError(
        f"a Download supports Path, str or bytes, not "
        f"{getattr(annotation, '__name__', annotation)}"
    )


def _shape_union(args: tuple[Any, ...]) -> _Shape:
    types: list[type] = []

    for option in args:
        shape = _shape(option)

        if not isinstance(shape, _Value):
            raise ReturnContractError(
                "a union inside a Download can only mix Path, str and bytes"
            )

        types.extend(shape.types)

    return _Value(tuple(dict.fromkeys(types)))


def _resolve(node: "_Node | None", value: Any) -> Any:
    if node is None:
        return value

    if isinstance(node, _Group):
        return _files(node, value)

    if isinstance(node, _Optional):
        return None if value is None else _resolve(node.node, value)

    if isinstance(node, _Each):
        if type(value) not in (list, tuple):
            raise ReturnContractError(
                f"expected a list or tuple of return elements, got "
                f"{_name_of(value)}"
            )

        return type(value)(_resolve(node.item, element) for element in value)

    if type(value) not in (list, tuple):
        raise ReturnContractError(
            f"expected {len(node.items)} return elements, got "
            f"{_name_of(value)}"
        )

    if len(value) != len(node.items):
        raise ReturnContractError(
            f"expected {len(node.items)} return elements, got {len(value)}"
        )

    return tuple(_resolve(item, element)
                 for item, element in zip(node.items, value))


def _files(group: _Group, value: Any) -> Any:
    if value is None:
        raise ReturnContractError(
            "None is not allowed for this Download return"
        )

    values = _flatten(group.shape, value)

    if isinstance(group.mark.filename, str) and len(values) > 1:
        raise ReturnContractError(
            f"the fixed filename {group.mark.filename!r} would name "
            f"{len(values)} files; pass a callable filename instead"
        )

    files = [
        _ReturnedFile(_source(item),
                      _name(group.mark.filename, item, index))
        for index, item in enumerate(values)
    ]

    return files[0] if isinstance(group.shape, _Value) else files


def _flatten(shape: _Shape, value: Any) -> list[Any]:
    if isinstance(shape, _Value):
        if not isinstance(value, shape.types):
            raise ReturnContractError(
                f"expected {_names_of(shape.types)} for Download, got "
                f"{_name_of(value)}"
            )

        return [value]

    if isinstance(shape, _Sequence):
        if type(value) not in (list, tuple):
            raise ReturnContractError(
                f"expected a list or tuple of files for Download, got "
                f"{_name_of(value)}"
            )

        return [item for element in value
                for item in _flatten(shape.item, element)]

    if type(value) not in (list, tuple):
        raise ReturnContractError(
            f"expected {len(shape.items)} files for Download, got "
            f"{_name_of(value)}"
        )

    if len(value) != len(shape.items):
        raise ReturnContractError(
            f"expected {len(shape.items)} files for Download, got {len(value)}"
        )

    return [item
            for element_shape, element in zip(shape.items, value)
            for item in _flatten(element_shape, element)]


def _source(value: Any) -> Path | bytes:
    if isinstance(value, bytes):
        return value

    return value if isinstance(value, Path) else Path(str(value))


def _name(
    filename: str | Callable[[object, int], str] | None,
    value: Any,
    index: int,
) -> str:
    if filename is None:
        if isinstance(value, (Path, str)):
            return _checked(Path(value).name, "Download filename")

        raise ReturnContractError(
            f"{_name_of(value)} downloads require a filename"
        )

    if isinstance(filename, str):
        return _checked(filename, "Download filename")

    try:
        produced = filename(value, index)
    except Exception as error:
        raise ReturnContractError(
            f"Download filename callable failed: "
            f"{type(error).__name__}: {error}"
        ) from error

    return _checked(produced,
                    "Download filename callable returned an invalid value")


def _checked(name: Any, what: str) -> str:
    if type(name) is not str:
        raise ReturnContractError(
            f"{what}: expected str, got {type(name).__name__}"
        )

    try:
        return segment_of(name, FILENAME_LIMIT)
    except ValueError as error:
        raise ReturnContractError(f"{what}: {error}, got {name!r}") from error
