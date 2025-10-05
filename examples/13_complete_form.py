from FuncToWeb import run, Color, Email, ImageFile
from typing import Annotated, Literal
from pydantic import Field
from datetime import date, time

def complete_profile(
    # Personal info
    full_name: Annotated[str, Field(min_length=3, max_length=50)] = "John Doe",
    email: Email = "john@example.com",
    birth_date: date = date(1990, 1, 1),
    
    # Preferences
    theme: Literal['light', 'dark', 'auto'] = 'auto',
    primary_color: Color = "#3b82f6",
    secondary_color: Color = "#10b981",
    
    # Settings
    age: Annotated[int, Field(ge=18, le=120)] = 25,
    height: Annotated[float, Field(ge=0.5, le=2.5)] = 1.75,
    wake_time: time = time(7, 0),
    
    # Options
    newsletter: bool = True,
    notifications: bool = False,
    
    # File
    avatar: ImageFile = None
):
    """Complete profile with all input types"""
    return {
        "full_name": full_name,
        "email": email,
        "birth_date": str(birth_date),
        "theme": theme,
        "colors": {
            "primary": primary_color,
            "secondary": secondary_color
        },
        "physical": {
            "age": age,
            "height": height
        },
        "wake_time": str(wake_time),
        "preferences": {
            "newsletter": newsletter,
            "notifications": notifications
        },
        "avatar": avatar
    }

run(complete_profile)