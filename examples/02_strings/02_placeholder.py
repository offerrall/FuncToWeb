from typing import Annotated
from func_to_web import run
from func_to_web.types import Placeholder

def search(query: Annotated[str, Placeholder("e.g. python web framework")]):
    return f"Searching: {query}"

run(search)
