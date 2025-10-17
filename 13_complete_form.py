from datetime import date, time

from func_to_web import Annotated, Field, Literal, run
from func_to_web.types import Color, Email, ImageFile


def complete_profile(
    full_name: Annotated[str, Field(min_length=3, max_length=50)] = "John Doe",
    email: Email = "john@example.com",
    birth_date: date = date(1990, 1, 1),
    theme: Literal['light', 'dark', 'auto'] = 'auto',
    primary_color: Color = "#3b82f6",
    age: Annotated[int, Field(ge=18, le=120)] = 25,
    height: Annotated[float, Field(ge=0.5, le=2.5)] = 1.75,
    wake_time: time = time(7, 0),
    notifications: bool = False,
    avatar: ImageFile | None = None,
    tags: list[str] | None = []
):
    """Complete profile with all input types"""
    return {
        "full_name": full_name,
        "email": email,
        "birth_date": str(birth_date),
        "theme": theme,
        "colors": {
            "primary": primary_color,
        },
        "physical": {
            "age": age,
            "height": height
        },
        "wake_time": str(wake_time),
        "preferences": {
            "notifications": notifications
        },
        "avatar": avatar,
        "tags": tags
    }

run(complete_profile)