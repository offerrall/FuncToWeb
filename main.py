from typing import Annotated, Literal
from pydantic import Field
from datetime import date, time
from FuncToWeb import run, Color, Email, ImageFile, DataFile, TextFile, DocumentFile

def create_profile(
    avatar: ImageFile,
    name: Annotated[str, Field(min_length=3, max_length=50)] = "John Doe",
    email: Email = "user@example.com",
    resume: DocumentFile = None,  # Acepta .pdf, .doc, .docx
    data_source: DataFile = None,  # Acepta .csv, .xlsx, .xls, .json
    notes: TextFile = None,  # Acepta .txt, .md, .log
    event_hour: time = time(14, 30),
    birth_date: date = date(1990, 1, 1),
    color: Color = "#10b981",
    age: Annotated[int, Field(ge=18, le=120)] = 25,
    theme: Literal['light', 'dark', 'auto'] = 'auto',
    newsletter: bool = True
):
    return {
        "name": name,
        "email": email,
        "avatar": avatar,
        "resume": resume,
        "data_source": data_source,
        "notes": notes,
        "birth_date": birth_date.isoformat(),
        "event_hour": event_hour.isoformat(),
        "color": color,
        "age": age,
        "theme": theme,
        "newsletter": newsletter
    }

run(create_profile)