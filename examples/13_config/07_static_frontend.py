from func_to_web import run

def search_users(q: str) -> list[dict]:
    """Called from a custom HTML/JS frontend via fetch()."""
    return [{"id": i, "name": f"{q}_{i}"} for i in range(5)]

# Drop your own index.html into ./site and your assets into ./assets
run(
    search_users,
    front_dir="./site",
    assets_dir="./assets",
)
