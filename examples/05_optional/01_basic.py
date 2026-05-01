from func_to_web import run

def search(
    query: str,
    limit: int | None = 10,
    filter: str | None = None,
):
    return f"q={query}, limit={limit}, filter={filter}"

run(search)
