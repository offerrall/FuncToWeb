"""An async def streams its prints exactly like a synchronous function."""

import asyncio
from typing import Annotated

from func_to_web import Max, Min, run

STEP_SECONDS = 0.2


async def fetch_pages(pages: Annotated[int, Min(1), Max(8)] = 4) -> str:
    """Report the progress of an awaited job."""
    print(f"fetching {pages} page(s)")

    for index in range(1, pages + 1):
        await asyncio.sleep(STEP_SECONDS)
        print(f"page {index} of {pages} ready")

    return f"{pages} page(s) processed"


if __name__ == "__main__":
    run(fetch_pages, title="Async progress")
