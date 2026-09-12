import test from "node:test";
import assert from "node:assert/strict";
import { installDocument, installWindow, postedMessages } from "./dom.mjs";
import { observeHeight } from "../../src/func_to_web/static/emit.js";

test("height observations coalesce, round up, deduplicate and shrink", () => {
    const document = installDocument();
    installWindow({ embedded: true });
    let height = 300.2;
    let changed;
    const scheduled = [];
    document.body.getBoundingClientRect = () => ({ height });
    globalThis.ResizeObserver = class {
        constructor(callback) { changed = callback; }
        observe(body) { assert.equal(body, document.body); }
    };
    globalThis.requestAnimationFrame = callback => {
        scheduled.push(callback);
        return scheduled.length;
    };
    try {
        observeHeight();
        changed();
        changed();
        assert.equal(scheduled.length, 1);
        scheduled.shift()();
        changed();
        scheduled.shift()();
        height = 140;
        changed();
        scheduled.shift()();
        assert.deepEqual(postedMessages().map(item => item.data), [
            { v: 1, kind: "resize", slug: "add", height: 301 },
            { v: 1, kind: "resize", slug: "add", height: 140 },
        ]);
    } finally {
        delete globalThis.ResizeObserver;
        delete globalThis.requestAnimationFrame;
    }
});
