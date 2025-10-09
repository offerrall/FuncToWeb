from func_to_web import Color, Email, run


def create_account(
    email: Email,
    favorite_color: Color = "#3b82f6", # default to a blue color and obligatory
    secondary_color: Color | None = "#10b981", # default to a green color and optional
    tertiary_color: Color | None = None, # no default and optional
):
    """Create account with special input types"""
    return f"Account created for {email} with colors {favorite_color} and {secondary_color} and {tertiary_color}"

run(create_account)