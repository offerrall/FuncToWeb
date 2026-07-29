import test from "node:test";
import assert from "node:assert/strict";

import { installDocument, makeElement } from "./dom.mjs";
import { installXhr, upload } from "./xhr.mjs";

const document = installDocument();
const xhr = installXhr();

const modal = makeElement("div", { className: "ftw-upload", hidden: true });
const dialog = makeElement("div", { className: "ftw-upload-dialog" });
const nameEl = makeElement("p", { className: "ftw-upload-name" });
const barEl = makeElement("progress", { className: "ftw-upload-bar" });
const percentEl = makeElement("p", { className: "ftw-upload-percent" });
const countEl = makeElement("p", { className: "ftw-upload-count" });
const errorEl = makeElement("p", { className: "ftw-upload-error", hidden: true });
const closeEl = makeElement("button", {
    className: "ftw-upload-close", hidden: true,
});

dialog.append(nameEl, barEl, percentEl, countEl, errorEl, closeEl);
modal.append(dialog);
document.body.append(modal);

const percents = [];
const bars = [];
const names = [];
const counts = [];

record(percentEl, "textContent", percents);
record(barEl, "value", bars);
record(nameEl, "textContent", names);
record(countEl, "textContent", counts);

const { runUploads } = await import("../../src/func_to_web/static/upload.js");

function record(element, property, history) {
    Object.defineProperty(element, property, {
        get: () => (history.length === 0 ? "" : history.at(-1)),
        set: (value) => {
            history.push(value);
        },
    });
}

test.beforeEach(() => {
    xhr.scenarios.length = 0;
    xhr.requests.length = 0;
    percents.length = 0;
    bars.length = 0;
    names.length = 0;
    counts.length = 0;
});

function ok() {
    return { outcome: "load", status: 200, response: { uploaded: true } };
}

function progressing(...loaded) {
    return { ...ok(), progress: loaded };
}


test("sends one request per upload and keeps their order", async () => {
    const completed = [];
    const uploads = [
        upload(completed, "a.txt", 10),
        upload(completed, "b.txt", 10),
        upload(completed, "c.txt", 10),
    ];

    xhr.scenarios.push(ok(), ok(), ok());

    assert.equal(await runUploads(uploads), true);
    assert.deepEqual(
        xhr.requests.map((request) => request.headers["X-File-Reference"]),
        ["ref-a.txt", "ref-b.txt", "ref-c.txt"]);
});

test("posts every file to the relative upload endpoint", async () => {
    const completed = [];
    const uploads = [upload(completed, "a.txt", 10)];

    xhr.scenarios.push(ok());

    await runUploads(uploads);

    const request = xhr.requests[0];

    assert.equal(request.method, "POST");
    assert.equal(request.url, "../upload");
    assert.equal(request.headers["Content-Type"], "application/octet-stream");
    assert.equal(request.responseType, "json");
    assert.equal(request.body, uploads[0].file);
});

test("announces the file name and the position of each upload", async () => {
    const completed = [];

    xhr.scenarios.push(ok(), ok());

    await runUploads([
        upload(completed, "a.txt", 10),
        upload(completed, "b.txt", 10),
    ]);

    assert.deepEqual(names, ["a.txt", "b.txt"]);
    assert.deepEqual(counts, ["1 of 2", "2 of 2"]);
});

test("calls complete only after a successful upload", async () => {
    const completed = [];

    xhr.scenarios.push(ok(), ok());

    await runUploads([
        upload(completed, "a.txt", 10),
        upload(completed, "b.txt", 10),
    ]);

    assert.deepEqual(completed, ["a.txt", "b.txt"]);
});

test("a failure stops the remaining uploads", async () => {
    const completed = [];

    xhr.scenarios.push(ok(), { outcome: "error" }, ok());

    const done = await runUploads([
        upload(completed, "a.txt", 10),
        upload(completed, "b.txt", 10),
        upload(completed, "c.txt", 10),
    ]);

    assert.equal(done, false);
    assert.equal(xhr.requests.length, 2);
});

test("a failed upload is never completed and neither are the next ones",
     async () => {
    const completed = [];

    xhr.scenarios.push(ok(), { outcome: "error" }, ok());

    await runUploads([
        upload(completed, "a.txt", 10),
        upload(completed, "b.txt", 10),
        upload(completed, "c.txt", 10),
    ]);

    assert.deepEqual(completed, ["a.txt"]);
});

test("hides the modal when every upload succeeds", async () => {
    const completed = [];

    xhr.scenarios.push(ok());

    assert.equal(await runUploads([upload(completed, "a.txt", 10)]), true);
    assert.equal(modal.hidden, true);
    assert.equal(errorEl.hidden, true);
    assert.equal(closeEl.hidden, true);
    assert.equal(modal.classList.contains("ftw-upload-failed"), false);
});

test("keeps the modal open and marked as failed after a failure", async () => {
    const completed = [];

    xhr.scenarios.push({ outcome: "error" });

    assert.equal(await runUploads([upload(completed, "a.txt", 10)]), false);
    assert.equal(modal.hidden, false);
    assert.equal(errorEl.hidden, false);
    assert.equal(closeEl.hidden, false);
    assert.equal(modal.classList.contains("ftw-upload-failed"), true);
});

test("shows the detail sent by the server in the failure message", async () => {
    const completed = [];

    xhr.scenarios.push({
        outcome: "load",
        status: 400,
        response: { detail: "file is too large" },
    });

    await runUploads([upload(completed, "big.bin", 10)]);

    assert.equal(errorEl.textContent,
                 "Upload failed: big.bin — file is too large");
});

test("falls back to a generic reason when the server sends no detail",
     async () => {
    const completed = [];

    xhr.scenarios.push({ outcome: "load", status: 500, response: null });

    await runUploads([upload(completed, "a.txt", 10)]);

    assert.equal(errorEl.textContent,
                 "Upload failed: a.txt — rejected by the server");
});

test("rejects a successful status that does not confirm the upload", async () => {
    const completed = [];

    xhr.scenarios.push({ outcome: "load", status: 200, response: { uploaded: false } });

    assert.equal(await runUploads([upload(completed, "a.txt", 10)]), false);
    assert.deepEqual(completed, []);
    assert.equal(errorEl.textContent,
                 "Upload failed: a.txt — rejected by the server");
});

test("ignores a non object detail sent by the server", async () => {
    const completed = [];

    xhr.scenarios.push({ outcome: "load", status: 400, response: { detail: 42 } });

    await runUploads([upload(completed, "a.txt", 10)]);

    assert.equal(errorEl.textContent,
                 "Upload failed: a.txt — rejected by the server");
});

test("reports a network error", async () => {
    const completed = [];

    xhr.scenarios.push({ outcome: "error" });

    assert.equal(await runUploads([upload(completed, "a.txt", 10)]), false);
    assert.equal(errorEl.textContent, "Upload failed: a.txt — network");
});

test("reports an aborted upload", async () => {
    const completed = [];

    xhr.scenarios.push({ outcome: "abort" });

    assert.equal(await runUploads([upload(completed, "a.txt", 10)]), false);
    assert.equal(errorEl.textContent, "Upload failed: a.txt — aborted");
});

test("a new run clears the error left by the previous one", async () => {
    const completed = [];

    xhr.scenarios.push({ outcome: "abort" }, ok());

    await runUploads([upload(completed, "a.txt", 10)]);
    await runUploads([upload(completed, "b.txt", 10)]);

    assert.equal(errorEl.textContent, "");
    assert.equal(errorEl.hidden, true);
    assert.equal(closeEl.hidden, true);
    assert.equal(modal.classList.contains("ftw-upload-failed"), false);
});

test("the close button hides the failed modal", async () => {
    const completed = [];

    xhr.scenarios.push({ outcome: "error" });

    await runUploads([upload(completed, "a.txt", 10)]);
    await closeEl.click();

    assert.equal(modal.hidden, true);
    assert.equal(errorEl.textContent, "");
    assert.equal(modal.classList.contains("ftw-upload-failed"), false);
});

test("escape hides the modal once an upload has failed", async () => {
    const completed = [];

    xhr.scenarios.push({ outcome: "error" });

    await runUploads([upload(completed, "a.txt", 10)]);

    document.dispatch("keydown", { key: "Escape" });

    assert.equal(modal.hidden, true);
});

test("escape does nothing while the modal is not in a failed state", async () => {
    const completed = [];

    xhr.scenarios.push(ok());

    await runUploads([upload(completed, "a.txt", 10)]);

    modal.hidden = false;
    document.dispatch("keydown", { key: "Escape" });

    assert.equal(modal.hidden, false);
});

test("another key never hides the failed modal", async () => {
    const completed = [];

    xhr.scenarios.push({ outcome: "error" });

    await runUploads([upload(completed, "a.txt", 10)]);

    document.dispatch("keydown", { key: "Enter" });

    assert.equal(modal.hidden, false);
});

test("the percent follows the bytes sent across every file", async () => {
    const completed = [];

    xhr.scenarios.push(progressing(50, 100), progressing(100));

    await runUploads([
        upload(completed, "a.txt", 100),
        upload(completed, "b.txt", 100),
    ]);

    assert.deepEqual(percents,
                     ["0%", "25%", "50%", "50%", "50%", "100%", "100%"]);
});

test("the progress bar mirrors the percent", async () => {
    const completed = [];

    xhr.scenarios.push(progressing(50));

    await runUploads([upload(completed, "a.txt", 100)]);

    assert.deepEqual(bars, [0, 50, 100]);
});

test("the percent is rounded to an integer", async () => {
    const completed = [];

    xhr.scenarios.push(progressing(1, 2));

    await runUploads([upload(completed, "a.txt", 3)]);

    assert.deepEqual(percents, ["0%", "33%", "67%", "100%"]);
});

test("the percent never leaves the zero to one hundred range", async () => {
    const completed = [];

    xhr.scenarios.push(progressing(-5, 999));

    await runUploads([upload(completed, "a.txt", 10)]);

    assert.deepEqual(percents, ["0%", "0%", "100%", "100%"]);
});

test("a total size of zero counts finished files instead of bytes", async () => {
    const completed = [];

    xhr.scenarios.push(progressing(0), progressing(0));

    await runUploads([
        upload(completed, "a.txt", 0),
        upload(completed, "b.txt", 0),
    ]);

    assert.deepEqual(percents, ["0%", "0%", "50%", "50%", "50%", "100%"]);
});

test("an empty list of uploads succeeds without sending anything", async () => {
    assert.equal(await runUploads([]), true);
    assert.equal(xhr.requests.length, 0);
    assert.equal(modal.hidden, true);
});
