import asyncio
import json
from collections.abc import Callable, Mapping
from dataclasses import fields, is_dataclass
from inspect import iscoroutinefunction
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from pytypehintweb import decode, plan_of

from func_to_web.models.file_defaults import with_references
from func_to_web.models.function import WebFunction, signature_with_prefill
from func_to_web.models.functions import FormAction
from func_to_web.models.return_parser import ReturnContractError, _ReturnedFile
from func_to_web.models.submit_defaults import as_submitted
from func_to_web.outputs import (
    DownloadOutput,
    download_output,
    form_output,
    output_of,
)
from func_to_web.web.messages import without_storage_paths
from func_to_web.web.print_capture import PrintCapture
from func_to_web.web.returned_files import store
from func_to_web.web.upload import reference_of, stored_file


OK: int = 200
UNPROCESSABLE: int = 422
FAILED: int = 500


async def execute(
    web_function: WebFunction,
    data: dict[str, Any],
    *,
    capture: PrintCapture | None = None,
    form: FormAction | None = None,
) -> tuple[dict[str, Any], int]:
    try:
        values = decode(web_function.schema, data,
                        file_resolver=stored_file)

        kwargs = web_function.schema.build(values)
    except Exception as error:
        return _failure(error, UNPROCESSABLE)

    try:
        value = await _call(web_function.fn, kwargs, capture)
    except Exception as error:
        return _failure(error, FAILED)

    try:
        if form is not None:
            return {"result": form_output(_opening(form, value))}, OK

        parser = web_function.return_parser
        resolved = value if parser is None else parser.resolved(value)

        return {"result": output_of(resolved, download=_download_of)}, OK
    except Exception as error:
        return _failure(error, FAILED)


def _opening(form: FormAction, value: Any) -> str:
    values = _prefill_values(value)

    try:
        plan = plan_of(signature_with_prefill(form.target.schema, values))
    except Exception as error:
        raise ReturnContractError(
            f"OpenForm returned invalid prefill: {error}"
        ) from error

    with_references(plan, _returned_reference)

    # The plan is built only to be read back: plan_of() is what writes a value
    # in its browser form, so the opening travels the same date text, enum name
    # and file reference the page itself would. What it writes it in is the
    # plan's grammar, and the destination reads the prefill as a submit, so
    # as_submitted() carries the one place the two spell a value differently.
    transport = {field["name"]: as_submitted(field["node"], field["default"])
                 for field in plan["fields"]
                 if field["name"] in values}

    query = {"prefill": json.dumps(transport, ensure_ascii=False)}

    if form.hidden:
        query["hidden"] = json.dumps(list(form.hidden))

    return f"../{form.target.slug}/?{urlencode(query)}"


def _prefill_values(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)

    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: getattr(value, item.name)
                for item in fields(value)}

    raise ReturnContractError(
        "OpenForm return must be a mapping or dataclass instance"
    )


def _returned_reference(where: tuple[str, ...], path: str) -> str:
    reference = reference_of(path)

    if reference is None:
        raise ReturnContractError(
            f"OpenForm returned a file outside the storage directory: "
            f"{Path(path).name!r}"
        )

    return reference


def _failure(error: Exception, status: int) -> tuple[dict[str, Any], int]:
    message = without_storage_paths(f"{type(error).__name__}: {error}")

    return {"error": message}, status


def _download_of(item: Any) -> DownloadOutput | None:
    if not isinstance(item, _ReturnedFile):
        return None

    return download_output(store(item.source, item.filename), item.filename)


async def _call(
    fn: Callable[..., Any],
    kwargs: dict[str, Any],
    capture: PrintCapture | None,
) -> Any:
    if iscoroutinefunction(fn):
        if capture is None:
            return await fn(**kwargs)

        with capture.capture_async():
            return await fn(**kwargs)

    return await asyncio.to_thread(_run_sync, fn, kwargs, capture)


def _run_sync(
    fn: Callable[..., Any],
    kwargs: dict[str, Any],
    capture: PrintCapture | None,
) -> Any:
    if capture is None:
        return fn(**kwargs)

    with capture.capture_sync():
        return fn(**kwargs)
