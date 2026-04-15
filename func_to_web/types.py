from pathlib import Path
from typing import Annotated, Literal, Callable, Any
from datetime import date, time
from dataclasses import dataclass

from pydantic import Field, BaseModel, model_validator
from pytypeinput.types import (Color, Email, ImageFile, VideoFile,
                         AudioFile, DataFile, TextFile, DocumentFile,
                         File, OptionalEnabled, OptionalDisabled, Dropdown,
                         IsPassword, Placeholder, Step, PatternMessage,
                         Description, Label, Rows, Slider)


class FileResponse(BaseModel):
    """Return a file from a function as a downloadable result.

    Provide either `data` or `path`, not both.

    Examples:
        return FileResponse(data=b"hello", filename="result.txt")
        return FileResponse(path="/tmp/report.pdf")
        return [FileResponse(...), FileResponse(...)]
    """
    data: bytes | None = None
    path: str | None = None
    filename: Annotated[str, Field(max_length=150)] | None= None

    @model_validator(mode="after")
    def _validate_data_or_path(self):
        if self.data is None and self.path is None:
            raise ValueError("Either 'data' or 'path' must be provided")
        if self.data is not None and self.path is not None:
            raise ValueError("Cannot provide both 'data' and 'path'")
        if self.data is not None and self.filename is None:
            raise ValueError("'filename' is required when providing 'data'")
        if self.path is not None and self.filename is None:
            self.filename = Path(self.path).name
        return self
    
@dataclass
class ActionTable:
    """Clickable table that navigates to another function with row data as prefill.

    Column names map to the destination function's parameter names.
    Non-matching columns are shown but ignored during navigation.

    Args:
        data: Table data. Accepts a callable (called at render time), a dict,
            a list of dicts, a list of lists, or any iterable.
            Compatible with any DB — SQLAlchemy, Pandas, TinyDB, Polars, etc.
        action: Destination function. Column names matching its params are prefilled.
        headers: Column names. Auto-derived from dict keys if omitted.
            Required when data is a list of lists.

    Examples:
        # Static data
        return ActionTable(data=DB, action=edit_user)

        # Live query — called at render time
        return ActionTable(data=get_users, action=edit_user)

        # SQLAlchemy
        return ActionTable(data=lambda: session.query(User).all(), action=edit_user)

    Note:
        ⚠️  Experimental. Works well with simple types (str, int, float).
        Files and complex types are not supported via URL prefill.
    """

    data: Any
    action: Callable
    headers: list[str] | None = None

    def __post_init__(self):
        if not hasattr(self.action, "__name__"):
            raise ValueError("action must be a named function")

        if callable(self.data):
            self.data = self.data()

        if isinstance(self.data, dict):
            rows = list(self.data.values())
        elif isinstance(self.data, list):
            rows = self.data
        else:
            rows = list(self.data)

        if not rows:
            raise ValueError("data cannot be empty")

        if isinstance(rows[0], dict):
            if self.headers is None:
                self.headers = list(rows[0].keys())
            self.rows = [[str(row[h]) for h in self.headers] for row in rows]
        else:
            if self.headers is None:
                raise ValueError("headers required when data is not dicts")
            self.rows = [[str(c) for c in row] for row in rows]

class Params:
    """Base class for grouping function parameters.
    
    Subclass this to define reusable parameter groups.
    Functoweb expands fields automatically into the form.

    Example:
        class UserData(Params):
            name: Annotated[str, Field(min_length=2)]
            email: Email
            role: Literal["admin", "user"] = "user"

        def create_user(data: UserData): ...
        def edit_user(id: int, data: UserData): ...
    """
    pass