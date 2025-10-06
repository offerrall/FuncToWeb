from func_to_web import Literal, run


def configure_app(
    theme: Literal['light', 'dark', 'auto'] = 'auto',
    language: Literal['en', 'es', 'fr', 'de'] = 'en',
    size: Literal['small', 'medium', 'large'] = 'medium'
):
    """Configure application settings"""
    return {
        "theme": theme,
        "language": language,
        "size": size,
        "message": f"App configured with {theme} theme in {language}"
    }

run(configure_app)