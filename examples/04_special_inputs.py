from func_to_web import Color, Email, run


def create_account(
    email: Email,
    favorite_color: Color = "#3b82f6",
    secondary_color: Color = "#10b981"
):
    """Create account with special input types"""
    return f"Account created for {email} with colors {favorite_color} and {secondary_color}"

run(create_account)