from func_to_web import run
from func_to_web.types import Color, Email, ImageFile

from typing_extensions import Literal

def create_account(
    email: Email, # Email input
    photo: ImageFile, # Image upload input
    favorite_color: Color, # Color picker input
    language: Literal['en', 'es', 'fr', 'de'] # Dropdown selection
):
    """Create account with special input types"""

    txt_return = f"Account created for {email} with photo {photo}, favorite color {favorite_color}, and language {language}."
    return txt_return

run(create_account)