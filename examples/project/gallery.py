"""Gallery — the outputs a CRUD never reaches, drawn inside the modal.

Adding a photo answers with a line of text, like every form so far. Resizing
one answers with the image *and* the file to keep, counting them answers with a
table, and thumbnailing several prints a line per file while it works: four
kinds of output, none of which a create-edit-delete ever produces, all of them
drawn by the page the host embeds.

That is why this host opens two kinds of modal. A confirmation closes on its
result, because the list behind it is the answer. Anything the user opened the
modal to read — the image, the table, the lines as they arrive — opens without
closeOnResult, since closing on the result would throw away the very thing it
was opened for. That is what the default being off is for.

Needs pillow and pandas, which the library neither requires nor imports.

Run:  python gallery.py
Open: http://127.0.0.1:8000/ (or /tools/doc, /api/photos)
"""

from itertools import count
from pathlib import Path
from tempfile import mkdtemp
from typing import Annotated

import pandas as pd
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from PIL import Image

from func_to_web import Download, FileHint, Label, Max, Min, Slider, app_of

Photo = Annotated[str, FileHint(extensions=(".png", ".jpg", ".jpeg", ".webp"))]

PHOTOS: dict[int, str] = {}
_ids = count(1)


def add_photo(photo: Annotated[Photo, Label("Photo")]) -> str:
    """Add a photo to the gallery."""
    photo_id = next(_ids)
    PHOTOS[photo_id] = photo

    return f"Photo {photo_id} added"


def resize_photo(
    photo: Annotated[Photo, Label("Photo")],
    width: Annotated[int, Min(16), Max(2000), Label("Width")] = 320,
    height: Annotated[int, Min(16), Max(2000), Label("Height")] = 320,
) -> tuple[Image.Image, Annotated[Path, Download()]]:
    """Resize a photo, returning the picture and the file to keep.

    Two outputs from one return, and the host opens this one without
    closeOnResult: an image and a download link live inside the modal, and
    closing on the result would take them away before they can be used.
    """
    with Image.open(photo) as picture:
        resized = picture.convert("RGB").resize((width, height))

    path = Path(mkdtemp()) / f"resized-{width}x{height}.png"
    resized.save(path)

    return resized, path


def stats() -> pd.DataFrame:
    """Summarize the gallery by file extension."""
    counted: dict[str, list[int]] = {}

    for path in PHOTOS.values():
        with Image.open(path) as picture:
            width, height = picture.size

        entry = counted.setdefault(Path(path).suffix.lower(), [0, 0])
        entry[0] += 1
        entry[1] += width * height

    return pd.DataFrame(
        [
            {
                "extension": extension,
                "photos": photos,
                "megapixels": round(pixels / 1_000_000, 2),
            }
            for extension, (photos, pixels) in sorted(counted.items())
        ],
        columns=["extension", "photos", "megapixels"],
    )


def bulk_thumbnails(
    photos: Annotated[list[Photo], Min(1), Max(8), Label("Photos")],
    size: Annotated[int, Min(32), Max(512), Slider(), Label("Side in pixels")] = 128,
) -> str:
    """Write one thumbnail per photo, reporting each one as it lands.

    The lines appear in the modal while the function runs, because the page it
    embeds is already talking to /invoke-stream. Streaming asks nothing of the
    host: print() is the whole API.
    """
    folder = Path(mkdtemp())

    for index, path in enumerate(photos, start=1):
        with Image.open(path) as picture:
            picture.thumbnail((size, size))
            picture.convert("RGB").save(folder / f"thumb-{index}.png")

        print(f"[{index}/{len(photos)}] {Path(path).name} at {size}px")

    return f"{len(photos)} thumbnail(s) written"


PAGE = """<!doctype html>
<meta charset="utf-8">
<title>Gallery</title>
<style>
body { font: 16px system-ui; max-width: 44rem; margin: 3rem auto; }
ul { display: flex; flex-wrap: wrap; gap: 1rem; list-style: none; padding: 0; }
li { display: flex; flex-direction: column; gap: .4rem; align-items: center; }
li img { width: 140px; height: 140px; border-radius: .4rem; object-fit: cover; }
</style>

<h1>Gallery</h1>
<p>Adding closes the modal on its result; reading one keeps it open.</p>

<button id="new" type="button">Add photo</button>
<button id="stats" type="button">Stats</button>
<button id="thumbs" type="button">Thumbnails</button>
<ul id="photos"></ul>

<script type="module">
import { openModal } from "/tools/static/sdk.js";

const grid = document.getElementById("photos");

async function photos() {
    const response = await fetch("/api/photos");

    return response.json();
}

async function run(url, prefill, hidden) {
    const modal = openModal(url, { prefill, hidden, closeOnResult: true });
    const { completed } = await modal.closed;

    if (completed) await refresh();
}

function show(url, prefill) {
    openModal(url, { prefill });
}

function cell(photo) {
    const item = document.createElement("li");
    const picture = document.createElement("img");

    picture.src = `/api/photo/${photo.photo_id}`;
    picture.alt = "";

    const resize = document.createElement("button");
    resize.type = "button";
    resize.textContent = "Resize";
    resize.addEventListener("click", () => show(
        "/tools/resize_photo", { photo: photo.reference }));

    item.append(picture, resize);

    return item;
}

async function refresh() {
    grid.replaceChildren(...(await photos()).map(cell));
}

document.getElementById("new").addEventListener(
    "click", () => run("/tools/add_photo"));
document.getElementById("stats").addEventListener(
    "click", () => show("/tools/stats"));
document.getElementById("thumbs").addEventListener(
    "click", () => show("/tools/bulk_thumbnails"));

await refresh();
</script>
"""

app = FastAPI()
app.mount("/tools", app_of([add_photo, resize_photo, stats, bulk_thumbnails]))


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """Serve the host page that opens each function in a modal."""
    return PAGE


@app.get("/api/photos")
def list_photos() -> list[dict]:
    return [
        {"photo_id": i, "reference": Path(path).name}
        for i, path in sorted(PHOTOS.items())
    ]


@app.get("/api/photo/{photo_id}")
def photo(photo_id: int) -> FileResponse:
    """Serve a photo from the path the application kept."""
    return FileResponse(PHOTOS[photo_id])


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
