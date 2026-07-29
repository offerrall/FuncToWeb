from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, TypeAlias

from func_to_web.models.function import WebFunction
from func_to_web.models.return_parser import OpenForm, ReturnContractError
from func_to_web.templates.doc import doc_of

DEFAULT_TITLE: str = "FuncToWeb"


@dataclass(frozen=True)
class FormAction:
    """Where the OpenForm of one function lands, already resolved.

    target is the WebFunction of this space that the opening shows, and
    hidden the parameters that opening does not display. WebFunctions.forms
    maps the slug of the function that returns the OpenForm to this.
    """

    target: WebFunction
    hidden: tuple[str, ...]


@dataclass(frozen=True)
class WebFunctions:
    """A prepared space: the functions served together, under one title.

    functions is a non-empty tuple of WebFunction with unique slugs; document
    holds the text /doc answers, forms the resolved OpenForm targets, and
    uploads and returns whether the space needs /upload and /returns.
    Raises TypeError or ValueError for an invalid tuple or title, and
    ReturnContractError for an OpenForm naming no registered target.
    """

    functions: tuple[WebFunction, ...]
    title: str = DEFAULT_TITLE
    document: str = field(init=False)
    forms: dict[str, FormAction] = field(init=False)
    uploads: bool = field(init=False)
    returns: bool = field(init=False)

    def __post_init__(self) -> None:
        if type(self.functions) is not tuple:
            raise TypeError("functions must be tuple")

        if not self.functions:
            raise ValueError("at least one function is required")

        if type(self.title) is not str:
            raise TypeError("title must be str")

        title = self.title.strip()

        if not title:
            raise ValueError("title cannot be empty")

        slugs: set[str] = set()

        for web_function in self.functions:
            if type(web_function) is not WebFunction:
                raise TypeError(
                    "functions must contain only WebFunction instances"
                )

            if web_function.slug in slugs:
                raise ValueError(
                    f"two functions share the slug {web_function.slug!r}"
                )

            slugs.add(web_function.slug)

        uploads = any(has_file(entry.plan) for entry in self.functions)
        returns = any(has_download(entry) for entry in self.functions)

        object.__setattr__(self, "title", title)
        object.__setattr__(self, "forms", _forms_of(self.functions))
        object.__setattr__(self, "uploads", uploads)
        object.__setattr__(self, "returns", returns)
        object.__setattr__(
            self,
            "document",
            doc_of(self.functions, title=title, uploads=uploads,
                   returns=returns),
        )


def has_file(value: Any) -> bool:
    if type(value) is dict:
        if value.get("kind") == "file":
            return True

        return any(has_file(item) for item in value.values())

    if type(value) is list:
        return any(has_file(item) for item in value)

    return False


def has_download(web_function: WebFunction) -> bool:
    parser = web_function.return_parser

    return parser is not None and parser.root is not None


def _forms_of(
    functions: tuple[WebFunction, ...],
) -> dict[str, FormAction]:
    actions: dict[str, FormAction] = {}

    for web_function in functions:
        parser = web_function.return_parser
        mark = None if parser is None else parser.form

        if mark is None:
            continue

        target = _target_of(mark, functions)

        _check_hidden(mark, target)

        actions[web_function.slug] = FormAction(target, mark.hidden)

    return actions


def _target_of(
    mark: OpenForm,
    functions: tuple[WebFunction, ...],
) -> WebFunction:
    if type(mark.target) is WebFunction:
        matches = [entry for entry in functions if entry is mark.target]
    else:
        matches = [entry for entry in functions if entry.fn is mark.target]

    if not matches:
        raise ReturnContractError(
            "OpenForm target is not registered in this space"
        )

    if len(matches) > 1:
        raise ReturnContractError(
            "OpenForm target matches more than one registered function"
        )

    return matches[0]


def _check_hidden(mark: OpenForm, target: WebFunction) -> None:
    names = {param.name for param in target.schema.params}

    for name in mark.hidden:
        if name not in names:
            raise ReturnContractError(
                f"unknown hidden field {name!r} for OpenForm target "
                f"{target.slug!r}"
            )


FunctionEntry: TypeAlias = Callable[..., Any] | WebFunction
FunctionInput: TypeAlias = (
    WebFunctions | FunctionEntry | Iterable[FunctionEntry]
)


def functions_of(
    values: Iterable[FunctionEntry],
    *,
    title: str = DEFAULT_TITLE,
) -> WebFunctions:
    prepared: list[WebFunction] = []

    for value in values:
        if type(value) is WebFunction:
            prepared.append(value)
        elif callable(value):
            prepared.append(WebFunction(value))
        else:
            raise TypeError(
                "entries must be callables or WebFunction instances"
            )

    return WebFunctions(tuple(prepared), title=title)


def space_of(
    value: FunctionInput,
    title: str | None,
) -> WebFunctions:
    if type(value) is WebFunctions:
        if title is not None:
            raise TypeError(
                "the prepared space already carries its title; "
                "set the title when creating WebFunctions"
            )

        return value

    resolved_title = DEFAULT_TITLE if title is None else title

    if type(value) is WebFunction or callable(value):
        return functions_of([value], title=resolved_title)

    if isinstance(value, Iterable):
        return functions_of(value, title=resolved_title)

    raise TypeError("entries must be callables or WebFunction instances")
