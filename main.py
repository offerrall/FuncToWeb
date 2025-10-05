from typing import Annotated, Literal
from pydantic import Field
from datetime import date, time
from FuncToWeb import run, Color, Email

def create_profile(
    name: Annotated[str, Field(min_length=3, max_length=50)] = "John Doe",
    email: Email = "user@example.com",
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
        "birth_date": birth_date.isoformat(),
        "event_hour": event_hour.isoformat(),
        "colors": color,
        "age": age,
        "theme": theme,
        "newsletter": newsletter
    }

run(create_profile)