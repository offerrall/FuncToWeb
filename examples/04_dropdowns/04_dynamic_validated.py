from typing import Annotated
from func_to_web import run
from func_to_web.types import Dropdown

def get_languages():
    return ["en", "es", "fr", "de"]

def translate(text: str, lang: Annotated[str, Dropdown(get_languages)]):
    if lang not in get_languages():
        raise ValueError(f"Invalid language: {lang}")
    return f"[{lang}] {text}"

run(translate)
