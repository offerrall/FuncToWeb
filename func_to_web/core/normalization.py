from typing import Any, Callable
from pathlib import Path

from ..models import FunctionMetadata, NormalizedInput
from .utils import slugify, detect_input_type, encode_favicon_to_base64, validate_css_vars


def normalize_input(
    user_input: Callable[..., Any] | FunctionMetadata | list,
    app_title: str | None = None,
    css_vars: dict[str, str] | None = None,
    favicon: str | Path | None = None,
    default_title: str = "Tools"
) -> NormalizedInput:
    """Normalize user input into the internal app config."""
    validate_css_vars(css_vars)

    input_type = detect_input_type(user_input)
    title = app_title if app_title is not None else default_title

    favicon_data_uri = None
    if favicon:
        favicon_data_uri = encode_favicon_to_base64(favicon)

    config = {
        "single_function": None,
        "items": None,
        "title": title,
        "css_vars": css_vars,
        "favicon_data_uri": favicon_data_uri,
    }

    if input_type == "single":
        config["single_function"] = normalize_function(user_input)
        if app_title is None:
            config["title"] = config["single_function"].name
    else:
        config["items"] = normalize_items(user_input)

    return NormalizedInput(**config)


def normalize_function(
    func_or_meta: Callable[..., Any] | FunctionMetadata
) -> FunctionMetadata:
    """Normalize a function-like input to FunctionMetadata."""
    if isinstance(func_or_meta, FunctionMetadata):
        return func_or_meta

    return FunctionMetadata(function=func_or_meta)


def normalize_items(items: list, current_path: str = "") -> list:
    """Normalize nested function/group input."""
    if not isinstance(items, list):
        raise TypeError(f"Items must be a list, got {type(items).__name__}")

    normalized = []

    for item in items:
        if isinstance(item, dict):
            if len(item) != 1:
                raise ValueError(
                    f"Group dict must have exactly one key-value pair, got {len(item)}"
                )

            subgroup_name = list(item.keys())[0]
            subgroup_items = list(item.values())[0]

            if not isinstance(subgroup_name, str):
                raise TypeError(
                    f"Group name must be string, got {type(subgroup_name).__name__}"
                )

            if not isinstance(subgroup_items, list):
                raise TypeError(
                    f"Group items must be a list, got {type(subgroup_items).__name__}"
                )

            subgroup_slug = slugify(subgroup_name)
            new_path = f"{current_path}/{subgroup_slug}" if current_path else subgroup_slug

            normalized.append({
                "type": "subgroup",
                "name": subgroup_name,
                "slug": subgroup_slug,
                "data": normalize_items(subgroup_items, new_path),
            })
        else:
            meta = normalize_function(item)
            normalized.append({
                "type": "function",
                "data": meta,
            })

    if not normalized:
        raise ValueError("Items list cannot be empty")

    return normalized


def build_navigation_structure(
    items: list,
    path_prefix: str = "",
    _seen_urls: set | None = None
) -> list[dict]:
    """Build the navigation tree and validate route uniqueness."""
    if _seen_urls is None:
        _seen_urls = set()

    nav_items = []

    for item in items:
        if item["type"] == "function":
            meta = item["data"]
            url = f"/{meta.slug}" if not path_prefix else f"/{path_prefix}/{meta.slug}"

            if url in _seen_urls:
                raise ValueError(
                    f"Duplicate URL '{url}' detected. "
                    f"Function '{meta.name}' conflicts with another function at the same path."
                )
            _seen_urls.add(url)

            nav_items.append({
                "type": "function",
                "name": meta.name,
                "slug": meta.slug,
                "description": meta.description,
                "url": url,
                "path": path_prefix,
                "hidden": meta.hidden,
            })
        else:
            subgroup_slug = item["slug"]
            sub_path = f"{path_prefix}/{subgroup_slug}" if path_prefix else subgroup_slug

            children = build_navigation_structure(item["data"], sub_path, _seen_urls)

            nav_items.append({
                "type": "subgroup",
                "name": item["name"],
                "slug": subgroup_slug,
                "is_group": True,
                "children": children,
                "path": sub_path,
            })

    return nav_items


def get_all_functions(items: list) -> list:
    """Collect all FunctionMetadata objects from a nested item tree."""
    functions = []
    for item in items:
        if item["type"] == "function":
            functions.append(item["data"])
        else:
            functions.extend(get_all_functions(item["data"]))
    return functions