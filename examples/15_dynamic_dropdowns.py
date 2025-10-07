from random import sample

from func_to_web import run, Literal

# Available options pool
THEMES = ['light', 'dark', 'auto', 'neon', 'retro']
SIZES = ['small', 'medium', 'large', 'xl']

# Dynamic option generators
def get_random_theme():
    return sample(THEMES, k=1)

def get_random_size():
    return sample(SIZES, k=1)


def configure_app(
    theme: Literal[get_random_theme],  # type: ignore
    size: Literal[get_random_size] = None,  # type: ignore
):
    """Configure app with dynamic dropdowns"""
    return {
        "theme": theme,
        "size": size,
        "message": f"Configured: {theme} theme, {size} size"
    }


run(configure_app)