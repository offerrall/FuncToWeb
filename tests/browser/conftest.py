import asyncio
import re
import subprocess
from html import unescape
from itertools import count
from pathlib import Path
from urllib.parse import urlencode

import pytest
from fastapi.staticfiles import StaticFiles

from shared import warm_uvicorn

HERE = Path(__file__).resolve().parent

warm_uvicorn()

RESULT = re.compile(r'<div id="result">(.*?)</div>', re.DOTALL)
LOG = re.compile(r'<pre id="log">(.*?)</pre>', re.DOTALL)

CHROME_FLAGS: tuple[str, ...] = (
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-sync",
    "--virtual-time-budget=20000",
    "--dump-dom",
)

DARK_SYSTEM: tuple[str, ...] = ("--blink-settings=preferredColorScheme=0",)
LIGHT_SYSTEM: tuple[str, ...] = ("--blink-settings=preferredColorScheme=1",)


@pytest.fixture
def verify(live_server, chrome, tmp_path):
    # A profile of its own per launch. Sharing one lets a Chrome that has not
    # finished exiting hold the lock, and the next launch then waits on it
    # instead of rendering.
    launches = count()

    def run(app, page, case, *, prefix="", flags=(), query=None):
        profile = tmp_path / f"chrome-profile-{next(launches)}"

        async def held(ms: int = 40) -> dict[str, int]:
            await asyncio.sleep(min(max(ms, 0), 500) / 1000)
            return {"ms": ms}

        app.add_api_route("/harness-hold", held, methods=["GET"])
        app.mount("/harness", StaticFiles(directory=HERE), name="harness")

        origin = live_server(app)

        params = {
            "base": f"{origin}{prefix}/",
            "hold": f"{origin}/harness-hold",
            "case": case,
            **(query or {}),
        }
        url = f"{origin}/harness/{page}?{urlencode(params)}"

        completed = subprocess.run(
            [str(chrome), f"--user-data-dir={profile}",
             *flags, *CHROME_FLAGS, url],
            capture_output=True,
            timeout=180,
        )

        dom = completed.stdout.decode("utf-8", "replace")

        found = RESULT.search(dom)
        recorded = LOG.search(dom)

        verdict = ("NO VERDICT" if found is None
                   else unescape(found.group(1)).strip())
        log = "" if recorded is None else unescape(recorded.group(1))

        if found is None:
            log = f"{log}\n\n--- dumped DOM ---\n{dom[:4000]}"

        return verdict, f"\n[{page} {case}] {verdict}\n{log}\n"

    return run
