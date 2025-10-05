from bbb import run, UI, Limits, Selected, Color, Email


def create_profile(
    name: UI[str, Limits(min_length=3, max_length=50)] = "John Doe",
    email: Email = "user@example.com",
    primary_color: Color = "#4f46e5",
    secondary_color: Color = "#10b981",
    age: UI[int, Limits(ge=18, le=120)] = 25,
    theme: Selected['light', 'dark', 'auto'] = 'auto',
    newsletter: bool = True
):
    return {
        "name": name,
        "email": email,
        "colors": {
            "primary": primary_color,
            "secondary": secondary_color
        },
        "age": age,
        "theme": theme,
        "newsletter": newsletter
    }

run(create_profile)