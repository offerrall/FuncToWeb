from typing import Annotated
from pydantic import Field

def IntUi(min: int = 0, max: int = 1000):
    return Annotated[int, Field(ge=min, le=max)]

def FloatUi(min: float = 0.0, max: float = 1000.0):
    return Annotated[float, Field(ge=min, le=max)]

def StrUi(min_length: int = 0, max_length: int = 100):
    return Annotated[str, Field(min_length=min_length, max_length=max_length)]

def BoolUi():
    return Annotated[bool, Field()]