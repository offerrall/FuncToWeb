import json
import inspect
from typing import get_type_hints

from fastapi import Request
from starlette.datastructures import UploadFile
from fastapi.responses import JSONResponse
from pytypeinput import ParamMetadata
from pytypeinput.analyzer import analyze_type
from pytypeinput.validate import validate_value

from .builder import render_page
from .models import FunctionMetadata, NormalizedInput
from .types import Params
from .core.save_file_handler import save_uploaded_file, cleanup_uploaded_file
from .call_function import call_function


def _reconstruct(params_class, model_data: dict):
    """Reconstruct a Params instance without calling __init__."""
    obj = object.__new__(params_class)
    for k, v in model_data.items():
        object.__setattr__(obj, k, v)
    return obj


def _analyze(func) -> tuple[list[ParamMetadata], dict]:
    """Analyze a function's parameters, expanding Params subclasses into individual fields.

    Returns the flat param list and a map of
    {original_param_name: (ParamsClass, [field_names])}.
    """
    hints = get_type_hints(func, include_extras=True)
    sig = inspect.signature(func)
    params = []
    params_map = {}

    for p in sig.parameters.values():
        if p.name not in hints:
            continue
        annotation = hints[p.name]
        if isinstance(annotation, type) and issubclass(annotation, Params):
            class_hints = get_type_hints(annotation, include_extras=True)
            model_params = []
            for fname, ftype in class_hints.items():
                if fname == "return":
                    continue
                default = getattr(annotation, fname, inspect.Parameter.empty)
                model_params.append(analyze_type(annotation=ftype, name=fname, default=default))
            params_map[p.name] = (annotation, [mp.name for mp in model_params])
            params.extend(model_params)
        else:
            params.append(analyze_type(annotation=annotation, name=p.name, default=p.default))

    return params, params_map


def validate_submit(
    params: list[ParamMetadata],
    values: dict,
    file_keys: set
) -> tuple[dict, dict]:
    """Validate submitted non-file values."""
    validated = {}
    errors = {}

    params_by_name = {p.name: p for p in params}

    for name in values:
        if name not in params_by_name:
            errors[name] = f"Unknown parameter: {name}"

    for param in params:
        name = param.name

        # File inputs are validated separately in submit_handler.
        if name in file_keys:
            continue

        if name in values:
            try:
                validated[name] = validate_value(param, values[name])
            except (ValueError, TypeError) as e:
                errors[name] = str(e)
        elif param.optional is not None:
            validated[name] = None
        else:
            errors[name] = "Missing required field"

    return validated, errors


def create_handlers(
    meta: FunctionMetadata,
    app_input: NormalizedInput,
    base_url: str
) -> tuple:
    """Create the page and submit handlers for a function."""
    # Analyze once; Params subclasses are expanded into individual fields.
    params, params_map = _analyze(meta.function)

    def refresh_params():
        """Refresh dynamic parameter choices."""
        for i in range(len(params)):
            params[i] = params[i].refresh_choices()

    async def page_handler():
        """Render the function page."""
        refresh_params()
        return render_page(params, meta, app_input, base_url=base_url)

    async def submit_handler(request: Request):
        """Validate input, save files, and execute the function."""
        saved_paths: list[str] = []

        try:
            form = await request.form()

            values_raw = form.get("values", "{}")
            values = json.loads(values_raw) if isinstance(values_raw, str) else {}

            # Group uploads by parameter name to support list file inputs.
            uploaded_files: dict[str, list[UploadFile]] = {}
            for key, value in form.multi_items():
                if isinstance(value, UploadFile):
                    uploaded_files.setdefault(key, []).append(value)

            validated, errors = validate_submit(
                params,
                values,
                file_keys=set(uploaded_files.keys())
            )

            params_by_name = {p.name: p for p in params}

            for name in set(uploaded_files):
                if name not in params_by_name:
                    errors[name] = f"Unknown parameter: {name}"

            for name in set(params_by_name) - set(values) - set(uploaded_files):
                param = params_by_name[name]
                if param.optional is not None:
                    validated[name] = None
                else:
                    errors[name] = "Missing required field"

            if errors:
                return JSONResponse({
                    "success": False,
                    "errors": errors,
                }, status_code=422)

            # Validate filenames/extensions before saving anything.
            for name, file_list in uploaded_files.items():
                param = params_by_name[name]
                filenames = [f.filename for f in file_list]
                value_to_validate = filenames if param.list is not None else filenames[0]

                try:
                    validate_value(param, value_to_validate)
                except (ValueError, TypeError) as e:
                    errors[name] = str(e)

            if errors:
                return JSONResponse({
                    "success": False,
                    "errors": errors,
                }, status_code=422)

            for name, file_list in uploaded_files.items():
                paths = []
                try:
                    for upload_file in file_list:
                        path = await save_uploaded_file(upload_file)
                        saved_paths.append(path)
                        paths.append(path)
                except ValueError as e:
                    for p in saved_paths:
                        cleanup_uploaded_file(p, force=True)
                    return JSONResponse({
                        "success": False,
                        "errors": {name: str(e)},
                    }, status_code=422)

                validated[name] = (
                    paths if params_by_name[name].list is not None else paths[0]
                )

            # Reconstruct Params instances from flat validated values.
            for param_name, (params_class, field_names) in params_map.items():
                model_data = {f: validated.pop(f) for f in field_names if f in validated}
                try:
                    validated[param_name] = _reconstruct(params_class, model_data)
                except (ValueError, TypeError) as e:
                    return JSONResponse({
                        "success": False,
                        "errors": {param_name: str(e)},
                    }, status_code=422)

            return await call_function(meta, validated, saved_paths)

        except Exception as e:
            for p in saved_paths:
                cleanup_uploaded_file(p, force=True)
            return JSONResponse({
                "success": False,
                "error": str(e),
            }, status_code=400)

    return page_handler, submit_handler