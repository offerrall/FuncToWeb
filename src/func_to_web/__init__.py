from pytypehint import (
    Choices,
    Description,
    Extra,
    FileHint,
    IsPassword,
    Label,
    Max,
    Min,
    MultipleOf,
    OptionalToggle,
    Pattern,
    Placeholder,
    Rows,
    SchemaTypeError,
    SchemaValueError,
    Slider,
    Step,
)
from pytypehintweb import COLOR_PATTERN, EMAIL_PATTERN, Color, Email

from func_to_web.config import __version__
from func_to_web.models.function import WebFunction, page_of
from func_to_web.models.functions import WebFunctions
from func_to_web.models.return_parser import (
    Download,
    OpenForm,
    ReturnContractError,
)
from func_to_web.templates.theme import Theme
from func_to_web.web.router import app_of
from func_to_web.web.run import run

__all__ = [
    "run",
    "app_of",
    "page_of",
    "WebFunction",
    "WebFunctions",
    "Download",
    "OpenForm",
    "ReturnContractError",
    "Theme",
    "__version__",
    "Min",
    "Max",
    "Choices",
    "MultipleOf",
    "Pattern",
    "FileHint",
    "Label",
    "Description",
    "Placeholder",
    "Step",
    "Slider",
    "IsPassword",
    "Rows",
    "Extra",
    "OptionalToggle",
    "Color",
    "Email",
    "COLOR_PATTERN",
    "EMAIL_PATTERN",
    "SchemaTypeError",
    "SchemaValueError",
]
