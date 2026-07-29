import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from inspect import cleandoc
from pathlib import Path
from typing import Any

from pytypehint import SchemaValueError, Signature, signature_of
from pytypehintweb import decode, plan_of

from func_to_web.models.file_defaults import with_references
from func_to_web.models.return_parser import ReturnParser, parser_of
from func_to_web.templates.page import labelled_plan, page_from_plan
from func_to_web.templates.theme import Theme, checked_theme
from func_to_web.web.upload import reference_of

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED_SLUGS = {"doc", "static", "upload", "returns"}


def _stored_reference(where: tuple[str, ...], path: str) -> str:
    reference = reference_of(path)

    if reference is None:
        raise SchemaValueError(
            f"file is not in the storage directory: {Path(path).name!r}",
            (*where, "default"),
        )

    return reference


def referenced_plan(signature: Signature) -> dict[str, Any]:
    """The plan of signature, with every file default written as a reference.

    A path the server holds never travels: what the plan publishes is the name
    storage knows the file by, and a file from anywhere else is refused here
    rather than later, when the path would already be out.
    """
    return with_references(plan_of(signature), _stored_reference)


@dataclass(frozen=True)
class WebFunction:
    """A callable prepared for the web: schema, plan and page compiled once.

    name, description and slug default to fn.__name__, fn.__doc__ and a slug
    derived from fn.__name__; capture_prints left as None inherits whatever
    the space decides. Raises TypeError for an invalid field type and
    ValueError for an empty or malformed name or slug.
    """

    fn: Callable[..., Any]
    name: str = ""
    description: str = ""
    slug: str = ""
    capture_prints: bool | None = None
    schema: Signature = field(init=False)
    plan: dict[str, Any] = field(init=False)
    html: str = field(init=False)
    return_parser: ReturnParser | None = field(init=False)

    def __post_init__(self) -> None:
        if not callable(self.fn):
            raise TypeError("fn must be callable")

        if type(self.name) is not str:
            raise TypeError("name must be str")

        if type(self.description) is not str:
            raise TypeError("description must be str")

        if type(self.slug) is not str:
            raise TypeError("slug must be str")

        if self.capture_prints is not None and type(self.capture_prints) is not bool:
            raise TypeError("capture_prints must be bool or None")

        declared = getattr(self.fn, "__name__", None)
        declared_name = declared if type(declared) is str else ""

        if (self.name == "" or self.slug == "") and not declared_name:
            raise TypeError(
                "fn must have a non-empty string __name__ when name or slug "
                "is not provided"
            )

        name = declared_name if self.name == "" else self.name

        if self.description == "":
            declared_description = getattr(self.fn, "__doc__", None)

            if (declared_description is not None
                    and type(declared_description) is not str):
                raise TypeError("fn.__doc__ must be str or None")

            description = declared_description or ""
        else:
            description = self.description

        derived_slug = re.sub(
            r"-+",
            "-",
            declared_name.lower().replace("_", "-"),
        ).strip("-")

        slug = derived_slug if self.slug == "" else self.slug

        name = name.strip()

        description = cleandoc(description).strip()

        if not name:
            raise ValueError("name cannot be empty")

        if self.slug == "" and SLUG_PATTERN.fullmatch(slug) is None:
            raise ValueError(
                f"cannot derive a valid slug from fn.__name__={declared_name!r}; "
                "pass slug explicitly"
            )

        if not slug.strip():
            raise ValueError("slug cannot be empty")

        if SLUG_PATTERN.fullmatch(slug) is None:
            raise ValueError(
                "slug must contain only lowercase letters, numbers and single hyphens"
            )

        if slug in RESERVED_SLUGS:
            raise ValueError(f"slug {slug!r} is reserved")

        schema = signature_of(self.fn)
        plan = labelled_plan(referenced_plan(schema), name=name,
                             description=description)
        html = page_from_plan(plan, name=name, description=description)

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "slug", slug)
        object.__setattr__(self, "schema", schema)
        object.__setattr__(self, "plan", plan)
        object.__setattr__(self, "html", html)
        object.__setattr__(self, "return_parser", parser_of(self.fn))


def signature_with_prefill(
    signature: Signature,
    prefill: Mapping[str, Any],
) -> Signature:
    names = {param.name for param in signature.params}

    for name in prefill:
        if name not in names:
            raise ValueError(f"unknown prefill field: {name!r}")

    params = tuple(
        replace(param, default=prefill[param.name])
        if param.name in prefill
        else param
        for param in signature.params
    )

    return replace(signature, params=params)


def build_prefill(
    signature: Signature,
    data: dict[str, Any],
    *,
    file_resolver: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    names = {param.name for param in signature.params}

    for name in data:
        if name not in names:
            raise ValueError(f"unknown prefill field: {name!r}")

    params = tuple(
        param for param in signature.params if param.name in data
    )

    partial = replace(signature, params=params)

    return partial.build(decode(partial, data, file_resolver=file_resolver))


def page_of(
    web_function: WebFunction,
    *,
    prefill: Mapping[str, Any] | None = None,
    hidden: Iterable[str] | None = None,
    theme: Theme = "system",
) -> str:
    """Render the complete HTML of one opening of a WebFunction.

    prefill proposes initial values as real Python objects and hidden names
    the parameters that opening does not show; neither changes the
    WebFunction. Raises TypeError for an invalid argument type and ValueError
    for an unknown prefill field.
    """
    if type(web_function) is not WebFunction:
        raise TypeError("web_function must be WebFunction")

    if type(hidden) is str:
        raise TypeError("hidden must be an iterable of str, not a single str")

    names = frozenset() if hidden is None else frozenset(hidden)

    if any(type(name) is not str for name in names):
        raise TypeError("hidden must contain only str")

    if not prefill and not names and checked_theme(theme) == "system":
        return web_function.html

    signature = (
        web_function.schema if not prefill
        else signature_with_prefill(web_function.schema, prefill)
    )

    return page_from_plan(
        referenced_plan(signature),
        name=web_function.name,
        description=web_function.description,
        hidden=names,
        theme=theme,
    )
