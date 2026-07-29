const modal = document.querySelector(".ftw-upload");
const nameEl = modal.querySelector(".ftw-upload-name");
const barEl = modal.querySelector(".ftw-upload-bar");
const percentEl = modal.querySelector(".ftw-upload-percent");
const countEl = modal.querySelector(".ftw-upload-count");
const errorEl = modal.querySelector(".ftw-upload-error");
const closeEl = modal.querySelector(".ftw-upload-close");

function reset() {
    modal.classList.remove("ftw-upload-failed");
    errorEl.textContent = "";
    errorEl.hidden = true;
    closeEl.hidden = true;
}

function hide() {
    modal.hidden = true;
    reset();
}

function fail(filename, reason) {
    errorEl.textContent = reason
        ? `Upload failed: ${filename} — ${reason}`
        : `Upload failed: ${filename}`;
    errorEl.hidden = false;
    closeEl.hidden = false;
    modal.classList.add("ftw-upload-failed");
}

closeEl.addEventListener("click", hide);

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modal.classList.contains("ftw-upload-failed")) {
        hide();
    }
});

function showPercent(value) {
    const percent = Math.min(100, Math.max(0, Math.round(value)));

    barEl.value = percent;
    percentEl.textContent = `${percent}%`;
}

function send(upload, onProgress) {
    return new Promise((resolve, reject) => {
        const request = new XMLHttpRequest();

        request.open("POST", "../upload");
        request.setRequestHeader("Content-Type", "application/octet-stream");
        request.setRequestHeader("X-File-Reference", upload.reference);
        request.responseType = "json";

        request.upload.addEventListener("progress", (event) => {
            onProgress(event.loaded);
        });

        request.addEventListener("load", () => {
            const data = request.response;

            if (
                request.status < 200 ||
                request.status >= 300 ||
                data === null ||
                typeof data !== "object" ||
                data.uploaded !== true
            ) {
                const detail = data !== null && typeof data === "object"
                    && typeof data.detail === "string" ? data.detail : null;

                reject(new Error(detail ?? "rejected by the server"));
                return;
            }

            resolve();
        });

        request.addEventListener("error", () => reject(new Error("network")));
        request.addEventListener("abort", () => reject(new Error("aborted")));

        request.send(upload.file);
    });
}

export async function runUploads(uploads) {
    const total = uploads.reduce((sum, upload) => sum + upload.file.size, 0);

    let sentBytes = 0;
    let finished = 0;

    const percentOf = (loaded) => (
        total === 0
            ? (finished / uploads.length) * 100
            : ((sentBytes + loaded) / total) * 100
    );

    reset();
    modal.hidden = false;

    for (const [index, upload] of uploads.entries()) {
        nameEl.textContent = upload.file.name;
        countEl.textContent = `${index + 1} of ${uploads.length}`;
        showPercent(percentOf(0));

        try {
            await send(upload, (loaded) => showPercent(percentOf(loaded)));
        } catch (error) {
            fail(upload.file.name, error.message);
            return false;
        }

        upload.complete();
        sentBytes += upload.file.size;
        finished += 1;
        showPercent(percentOf(0));
    }

    hide();

    return true;
}
