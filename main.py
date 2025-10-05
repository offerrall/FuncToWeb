from bbb import run, UI, Limits, Selected, Color, Email
from datetime import date, time

def create_profile(
    primary_color: Color,
    name: UI[str, Limits(min_length=3, max_length=50)] = "John Doe",
    email: Email = "user@example.com",
    event_hour: time = time(14, 30),
    birth_date: date = date(1990, 1, 1),
    secondary_color: Color = "#10b981",
    age: UI[int, Limits(ge=18, le=120)] = 25,
    theme: Selected['light', 'dark', 'auto'] = 'auto',
    newsletter: bool = True
):
    return {
        "name": name,
        "email": email,
        "birth_date": birth_date.isoformat(),
        "event_hour": event_hour.isoformat(),
        "colors": {
            "primary": primary_color,
            "secondary": secondary_color
        },
        "age": age,
        "theme": theme,
        "newsletter": newsletter
    }

run(create_profile)