from typing import Annotated
from pydantic import Field

COLOR_PATTERN = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
EMAIL_PATTERN = r'^[^@]+@[^@]+\.[^@]+$'

def _file_pattern(*extensions):
    """Generate regex pattern for file extensions."""
    exts = [e.lstrip('.').lower() for e in extensions]
    return r'^.+\.(' + '|'.join(exts) + r')$'


Color = Annotated[str, Field(pattern=COLOR_PATTERN)]
Email = Annotated[str, Field(pattern=EMAIL_PATTERN)]
ImageFile = Annotated[str, Field(pattern=_file_pattern('png', 'jpg', 'jpeg', 'gif', 'webp'))]
DataFile = Annotated[str, Field(pattern=_file_pattern('csv', 'xlsx', 'xls', 'json'))]
TextFile = Annotated[str, Field(pattern=_file_pattern('txt', 'md', 'log'))]
DocumentFile = Annotated[str, Field(pattern=_file_pattern('pdf', 'doc', 'docx'))]


class _OptionalEnabledMarker:
    """Internal marker for OptionalEnabled"""
    pass

class _OptionalDisabledMarker:
    """Internal marker for OptionalDisabled"""
    pass


OptionalEnabled = Annotated[None, _OptionalEnabledMarker()]
OptionalDisabled = Annotated[None, _OptionalDisabledMarker()]