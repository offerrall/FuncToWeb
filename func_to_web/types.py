from typing import Annotated, Callable
from dataclasses import dataclass
from pydantic import Field, BaseModel
from pydantic import model_validator
from datetime import date, time

COLOR_PATTERN = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
EMAIL_PATTERN = r'^[^@]+@[^@]+\.[^@]+$'
ANY_FILE_PATTERN = r'^.+$'

def _file_pattern(*extensions):
    """Generate regex pattern for file extensions."""
    exts = [e.lstrip('.').lower() for e in extensions]
    return r'^.+\.(' + '|'.join(exts) + r')$'

Color = Annotated[str, Field(pattern=COLOR_PATTERN)]
Email = Annotated[str, Field(pattern=EMAIL_PATTERN)]
ImageFile = Annotated[str, Field(pattern=_file_pattern('png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'svg', 'ico', 'heic', 'avif', 'raw', 'psd'))]
VideoFile = Annotated[str, Field(pattern=_file_pattern('mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm', 'mpeg', 'mpg'))]
AudioFile = Annotated[str, Field(pattern=_file_pattern('mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a'))]
DataFile = Annotated[str, Field(pattern=_file_pattern('csv', 'xlsx', 'xls', 'json', 'xml', 'yaml', 'yml'))]
TextFile = Annotated[str, Field(pattern=_file_pattern('txt', 'md', 'log', 'rtf'))]
DocumentFile = Annotated[str, Field(pattern=_file_pattern('pdf', 'doc', 'docx', 'odt', 'ppt', 'pptx', 'odp', 'xls', 'xlsx', 'ods'))]
File = Annotated[str, Field(pattern=ANY_FILE_PATTERN)]

class _OptionalEnabledMarker:
    """Internal marker for OptionalEnabled"""
    pass

class _OptionalDisabledMarker:
    """Internal marker for OptionalDisabled"""
    pass

class FileResponse(BaseModel):
    """Model for file response - accepts either binary data or file path."""
    data: bytes | None = None
    path: str | None = None
    filename: Annotated[str, Field(max_length=150)]
    
    @model_validator(mode='after')
    def validate_data_or_path(self):
        """Ensure exactly one of data or path is provided."""
        if self.data is None and self.path is None:
            raise ValueError("Either 'data' or 'path' must be provided")
        if self.data is not None and self.path is not None:
            raise ValueError("Cannot provide both 'data' and 'path'")
        return self

@dataclass
class Dropdown():
    data_function: Callable[[], list]

OptionalEnabled = Annotated[None, _OptionalEnabledMarker()]
OptionalDisabled = Annotated[None, _OptionalDisabledMarker()]