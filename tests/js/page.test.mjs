import test from "node:test";
import assert from "node:assert/strict";

import "./loader.mjs";
import {
    installDocument, installWindow, makeElement, find, postedMessages,
} from "./dom.mjs";
import {
    installClipboard, installObjectUrls, installTimers, installFetch, streamOf,
    splitBytes, sse,
} from "./browser.mjs";
import { installXhr, upload } from "./xhr.mjs";
import { form, reset } from "./form-stub.mjs";

const INVALID = "Invalid server response";
const PAGE = "../../src/func_to_web/static/page.js";

const xhr = installXhr();

let instance = 0;


function modalTree() {
    const modal = makeElement("div", { className: "ftw-upload", hidden: true });

    modal.append(
        makeElement("p", { className: "ftw-upload-name" }),
        makeElement("progress", { className: "ftw-upload-bar" }),
        makeElement("p", { className: "ftw-upload-percent" }),
        makeElement("p", { className: "ftw-upload-count" }),
        makeElement("p", { className: "ftw-upload-error", hidden: true }),
        makeElement("button", { className: "ftw-upload-close", hidden: true }),
    );

    return modal;
}


async function load(options = {}) {
    const document = installDocument();

    installClipboard();
    installObjectUrls();
    installTimers();

    xhr.scenarios.length = 0;
    xhr.requests.length = 0;

    reset();
    Object.assign(form, options.form ?? {});

    const submit = makeElement("button", { id: "submit" });
    const result = makeElement("div", { id: "result" });
    const fields = makeElement("div", { id: "fields" });

    document.byId.set("functoweb-plan", makeElement("script", {
        textContent: JSON.stringify(options.plan ?? { fields: [] }),
    }));
    document.byId.set("functoweb-hidden", makeElement("script", {
        textContent: JSON.stringify(options.hidden ?? []),
    }));
    document.byId.set("submit", submit);
    document.byId.set("result", result);
    document.byId.set("fields", fields);
    document.body.append(modalTree());

    const page = {
        document,
        submit,
        result,
        fields,
        assigned: installWindow({
            embedded: options.embedded ?? false,
            pathname: options.pathname ?? "/tools/add/",
        }),
        posted: postedMessages(),
        chunks: [],
        response: null,
        seen: [],
        calls: [],
    };

    page.calls = installFetch(async () => {
        page.seen.push({ disabled: submit.disabled });

        if (page.response instanceof Error) throw page.response;

        return page.response ?? { ok: true, body: streamOf(page.chunks) };
    });

    page.send = async (chunks) => {
        page.chunks = chunks;

        await submit.click();

        return page.cards();
    };

    page.cards = () => page.result.children.map(
        (child) => [...child.classes()].find((name) => name !== "ftw-output"));

    page.message = () => {
        const values = find(page.result, ".ftw-output-value");

        return values.length === 0 ? null : values.at(-1).textContent;
    };

    instance += 1;

    await import(`${PAGE}?instance=${instance}`);

    return page;
}


async function resultOf(envelope, extra = []) {
    const page = await load();

    return { page, cards: await page.send([...extra, sse("result", envelope)]) };
}


test("renders the output carried by a well formed stream", async () => {
    const page = await load();
    const cards = await page.send([
        sse("start", {}),
        sse("result", { result: { type: "text", value: "hello" } }),
    ]);

    assert.deepEqual(cards, ["ftw-output-text"]);
    assert.equal(page.message(), "hello");
});

test("posts the form body to the streaming endpoint", async () => {
    const page = await load({ form: { body: { a: 1 } } });

    await page.send([sse("result", { result: { type: "text", value: "x" } })]);

    assert.equal(page.calls.length, 1);
    assert.equal(page.calls[0].url, "invoke-stream");
    assert.equal(page.calls[0].options.method, "POST");
    assert.equal(page.calls[0].options.body, JSON.stringify({ a: 1 }));
    assert.equal(page.calls[0].options.headers.Accept, "text/event-stream");
});

test("shows a running card while the stream is open", async () => {
    const page = await load();
    const seen = [];

    page.chunks = [sse("start", {}), sse("result", { result: null })];

    const original = page.result.replaceChildren.bind(page.result);

    page.result.replaceChildren = (...nodes) => {
        seen.push(nodes.map(
            (node) => [...node.classes()].find((name) => name !== "ftw-output")));
        original(...nodes);
    };

    await page.submit.click();

    assert.deepEqual(seen[0], ["ftw-output-running"]);
});

test("reconstructs an event whose data spans several lines", async () => {
    const page = await load();
    const cards = await page.send([
        'event: result\ndata: {"result":\ndata: {"type":"text","value":"multi"}}\n\n',
    ]);

    assert.deepEqual(cards, ["ftw-output-text"]);
    assert.equal(page.message(), "multi");
});

test("reconstructs an event split into single byte chunks", async () => {
    const page = await load();
    const cards = await page.send(
        splitBytes(sse("result", { result: { type: "text", value: "piña ✅" } }), 1));

    assert.deepEqual(cards, ["ftw-output-text"]);
    assert.equal(page.message(), "piña ✅");
});

test("reconstructs events when a chunk ends inside the blank separator",
     async () => {
    const page = await load();
    const body = 'event: result\ndata: {"result":{"type":"text","value":"cut"}}\n';
    const cards = await page.send([body, "\n"]);

    assert.deepEqual(cards, ["ftw-output-text"]);
    assert.equal(page.message(), "cut");
});

test("reconstructs two events arriving inside a single chunk", async () => {
    const page = await load();
    const cards = await page.send([
        sse("print", { text: "one" })
        + sse("result", { result: { type: "text", value: "two" } }),
    ]);

    assert.deepEqual(cards, ["ftw-output-stdout", "ftw-output-text"]);
});

test("accepts an event using crlf line endings", async () => {
    const page = await load();
    const cards = await page.send([
        'event: result\r\ndata: {"result":{"type":"text","value":"crlf"}}\r\n\r\n',
    ]);

    assert.deepEqual(cards, ["ftw-output-text"]);
    assert.equal(page.message(), "crlf");
});

test("BUG: a crlf terminator split across chunks loses the whole event",
     async () => {
    const page = await load();
    const body = 'event: result\r\ndata: {"result":{"type":"text","value":"crlf"}}\r\n\r';
    const cards = await page.send([body, "\n"]);

    assert.deepEqual(cards, ["ftw-output-text"]);
    assert.equal(page.message(), "crlf");
});

test("treats invalid json in a data line as a missing payload", async () => {
    const page = await load();
    const cards = await page.send(["event: result\ndata: {not json}\n\n"]);

    assert.deepEqual(cards, ["ftw-output-error"]);
    assert.equal(page.message(), INVALID);
});

test("treats an event with no data lines as a missing payload", async () => {
    const page = await load();

    await page.send(["event: result\n\n"]);

    assert.equal(page.message(), INVALID);
});

test("ignores a block that carries no event name", async () => {
    const page = await load();
    const cards = await page.send([
        'data: {"result":{"type":"text","value":"orphan"}}\n\n',
        sse("result", { result: { type: "text", value: "kept" } }),
    ]);

    assert.deepEqual(cards, ["ftw-output-text"]);
    assert.equal(page.message(), "kept");
});

test("ignores comment blocks used as heartbeats", async () => {
    const page = await load();
    const cards = await page.send([
        ": keep alive\n\n",
        sse("result", { result: { type: "text", value: "kept" } }),
    ]);

    assert.deepEqual(cards, ["ftw-output-text"]);
});

test("keeps a payload that contains the literal data prefix", async () => {
    const page = await load();
    const text = "data: not an event\ndata: neither is this";

    await page.send([sse("result", { result: { type: "text", value: text } })]);

    assert.equal(page.message(), text);
});

test("keeps a printed chunk that contains the literal data prefix", async () => {
    const page = await load();

    await page.send([
        sse("print", { text: "data: still text\n" }),
        sse("result", { result: { type: "text", value: "x" } }),
    ]);

    assert.equal(find(page.result, ".ftw-output-value")[0].textContent,
                 "data: still text\n");
});

test("ignores a trailing block that never reaches a blank line", async () => {
    const page = await load();
    const cards = await page.send([
        sse("result", { result: { type: "text", value: "done" } }),
        'event: result\ndata: {"result":{"type":"text","value":"cut off"}}',
    ]);

    assert.deepEqual(cards, ["ftw-output-text"]);
    assert.equal(page.message(), "done");
});

test("reports an invalid response when the stream carries no result",
     async () => {
    const page = await load();
    const cards = await page.send([sse("start", {})]);

    assert.deepEqual(cards, ["ftw-output-error"]);
    assert.equal(page.message(), INVALID);
});

test("reports an invalid response when the stream is empty", async () => {
    const page = await load();

    await page.send([]);

    assert.equal(page.message(), INVALID);
});

test("accumulates printed chunks in a single growing stdout card", async () => {
    const page = await load();
    const cards = await page.send([
        sse("print", { text: "one\n" }),
        sse("print", { text: "two\n" }),
        sse("print", { text: "three" }),
        sse("result", { result: { type: "text", value: "done" } }),
    ]);

    assert.deepEqual(cards, ["ftw-output-stdout", "ftw-output-text"]);

    const stdout = find(page.result, ".ftw-output-stdout")[0];

    assert.equal(find(stdout, ".ftw-output-value").length, 1);
    assert.equal(find(stdout, ".ftw-output-value")[0].textContent,
                 "one\ntwo\nthree");
});

test("keeps the stdout card alongside a failing result", async () => {
    const page = await load();
    const cards = await page.send([
        sse("print", { text: "noise" }),
        sse("result", { error: "boom" }),
    ]);

    assert.deepEqual(cards, ["ftw-output-stdout", "ftw-output-error"]);
});

test("shows no stdout card when nothing was printed", async () => {
    const page = await load();
    const cards = await page.send([
        sse("result", { result: { type: "text", value: "x" } }),
    ]);

    assert.deepEqual(cards, ["ftw-output-text"]);
});

test("ignores a print event whose text is not a string", async () => {
    const page = await load();
    const cards = await page.send([
        sse("print", { text: 42 }),
        sse("print", {}),
        sse("result", { result: { type: "text", value: "x" } }),
    ]);

    assert.deepEqual(cards, ["ftw-output-text"]);
});

test("reports an invalid response when the request cannot be sent", async () => {
    const page = await load();

    page.response = new Error("offline");

    await page.submit.click();

    assert.deepEqual(page.cards(), ["ftw-output-error"]);
    assert.equal(page.message(), INVALID);
});

test("reports an invalid response when the status is not ok", async () => {
    const page = await load();

    page.response = { ok: false, body: streamOf([]) };

    await page.submit.click();

    assert.equal(page.message(), INVALID);
});

test("reports an invalid response when the body is missing", async () => {
    const page = await load();

    page.response = { ok: true, body: null };

    await page.submit.click();

    assert.equal(page.message(), INVALID);
});

test("rejects an output whose type is unknown", async () => {
    const { page, cards } = await resultOf({
        result: { type: "hologram", value: "x" },
    });

    assert.deepEqual(cards, ["ftw-output-error"]);
    assert.equal(page.message(), INVALID);
});

test("rejects an output whose value is not a string", async () => {
    const { page } = await resultOf({ result: { type: "text", value: 7 } });

    assert.equal(page.message(), INVALID);
});

test("rejects an output that is not an object", async () => {
    const { page } = await resultOf({ result: "plain" });

    assert.equal(page.message(), INVALID);
});

test("rejects a null output", async () => {
    const { page } = await resultOf({ result: null });

    assert.equal(page.message(), INVALID);
});

test("accepts a well formed table", async () => {
    const { page, cards } = await resultOf({
        result: { type: "table", headers: ["a", "b"], rows: [["1", "2"]] },
    });

    assert.deepEqual(cards, ["ftw-output-table"]);
    assert.equal(find(page.result, "th").length, 2);
    assert.equal(find(page.result, "tbody")[0].children.length, 1);
});

test("accepts a table with no rows", async () => {
    const { cards } = await resultOf({
        result: { type: "table", headers: ["a"], rows: [] },
    });

    assert.deepEqual(cards, ["ftw-output-table"]);
});

test("rejects a table whose headers are not strings", async () => {
    const { page } = await resultOf({
        result: { type: "table", headers: ["a", 2], rows: [["1", "2"]] },
    });

    assert.equal(page.message(), INVALID);
});

test("rejects a table whose headers are not an array", async () => {
    const { page } = await resultOf({
        result: { type: "table", headers: "ab", rows: [] },
    });

    assert.equal(page.message(), INVALID);
});

test("rejects a table whose rows are not arrays of strings", async () => {
    const { page } = await resultOf({
        result: { type: "table", headers: ["a"], rows: [["1"], [2]] },
    });

    assert.equal(page.message(), INVALID);
});

test("rejects a table whose rows are not an array", async () => {
    const { page } = await resultOf({
        result: { type: "table", headers: ["a"], rows: { "0": ["1"] } },
    });

    assert.equal(page.message(), INVALID);
});

test("rejects a table row holding a nested array", async () => {
    const { page } = await resultOf({
        result: { type: "table", headers: ["a"], rows: [[["1"]]] },
    });

    assert.equal(page.message(), INVALID);
});

test("accepts a download carrying a reference and a filename", async () => {
    const { page, cards } = await resultOf({
        result: { type: "download", value: "ref-1", filename: "out.csv" },
    });

    assert.deepEqual(cards, ["ftw-output-download"]);
    assert.equal(find(page.result, ".ftw-download")[0].href, "../returns/ref-1");
});

test("rejects a download without a filename", async () => {
    const { page } = await resultOf({
        result: { type: "download", value: "ref-1" },
    });

    assert.equal(page.message(), INVALID);
});

test("rejects a download whose filename is empty", async () => {
    const { page } = await resultOf({
        result: { type: "download", value: "ref-1", filename: "" },
    });

    assert.equal(page.message(), INVALID);
});

test("rejects a download whose filename is not a string", async () => {
    const { page } = await resultOf({
        result: { type: "download", value: "ref-1", filename: 3 },
    });

    assert.equal(page.message(), INVALID);
});

test("accepts an image output", async () => {
    const { page, cards } = await resultOf({
        result: { type: "image", value: "data:image/png;base64,AA" },
    });

    assert.deepEqual(cards, ["ftw-output-image"]);
    assert.equal(find(page.result, ".ftw-output-img")[0].alt, "");
});

test("navigates to a form output and shows a waiting card", async () => {
    const { page, cards } = await resultOf({
        result: { type: "form", href: "../step-two" },
    });

    assert.deepEqual(cards, ["ftw-output-form"]);
    assert.deepEqual(page.assigned, ["../step-two"]);
});

test("rejects a form output without an href", async () => {
    const { page } = await resultOf({ result: { type: "form" } });

    assert.equal(page.message(), INVALID);
    assert.deepEqual(page.assigned, []);
});

test("rejects a form output whose href is empty", async () => {
    const { page } = await resultOf({ result: { type: "form", href: "" } });

    assert.equal(page.message(), INVALID);
    assert.deepEqual(page.assigned, []);
});

test("does not navigate when a form arrives beside another output", async () => {
    const { page } = await resultOf({
        result: [
            { type: "form", href: "../step-two" },
            { type: "text", value: "x" },
        ],
    });

    assert.equal(page.message(), INVALID);
    assert.deepEqual(page.assigned, []);
});

test("renders every output of an array result", async () => {
    const { cards } = await resultOf({
        result: [
            { type: "text", value: "a" },
            { type: "image", value: "b.png" },
            { type: "table", headers: ["h"], rows: [["r"]] },
        ],
    });

    assert.deepEqual(cards,
                     ["ftw-output-text", "ftw-output-image", "ftw-output-table"]);
});

test("rejects the whole array when one output is invalid", async () => {
    const { page, cards } = await resultOf({
        result: [
            { type: "text", value: "a" },
            { type: "text", value: 2 },
        ],
    });

    assert.deepEqual(cards, ["ftw-output-error"]);
    assert.equal(page.message(), INVALID);
});

test("accepts an empty array result", async () => {
    const { cards } = await resultOf({ result: [] });

    assert.deepEqual(cards, []);
});

test("shows the error carried by the envelope", async () => {
    const { page, cards } = await resultOf({ error: "ValueError: nope" });

    assert.deepEqual(cards, ["ftw-output-error"]);
    assert.equal(page.message(), "ValueError: nope");
});

test("rejects an envelope carrying a result and an error at once", async () => {
    const { page } = await resultOf({
        result: { type: "text", value: "x" },
        error: "boom",
    });

    assert.equal(page.message(), INVALID);
});

test("rejects an envelope carrying neither a result nor an error", async () => {
    const { page } = await resultOf({ status: "ok" });

    assert.equal(page.message(), INVALID);
});

test("rejects an envelope that is not an object", async () => {
    const page = await load();

    await page.send(["event: result\ndata: \"plain\"\n\n"]);

    assert.equal(page.message(), INVALID);
});

test("shows only the fields that the page does not hide", async () => {
    const widgets = {
        a: makeElement("div", { id: "wa" }),
        b: makeElement("div", { id: "wb" }),
    };

    const page = await load({
        plan: { fields: [{ name: "a", label: "A" }, { name: "b", label: "B" }] },
        hidden: ["b"],
        form: {
            fields: [
                { name: "a", widget: { el: widgets.a } },
                { name: "b", widget: { el: widgets.b } },
            ],
        },
    });

    assert.deepEqual(page.fields.children.map((child) => child.id), ["wa"]);
});

test("does not invoke the server when the form is not ready", async () => {
    const page = await load({
        plan: { fields: [{ name: "a", label: "Age" }] },
        form: {
            ready: false,
            fields: [{
                name: "a",
                widget: { el: makeElement("div"), hasError: () => false, isReady: () => false },
            }],
        },
    });

    await page.submit.click();

    assert.equal(page.calls.length, 0);
    assert.equal(form.errorsShown, 1);
});

test("lists the fields to fix by their label", async () => {
    const page = await load({
        plan: { fields: [{ name: "a", label: "Age" }] },
        form: {
            ready: false,
            fields: [{
                name: "a",
                widget: { el: makeElement("div"), hasError: () => true, isReady: () => false },
            }],
        },
    });

    await page.submit.click();

    assert.equal(page.message(), "Fix: Age");
});

test("lists the fields to complete by their label", async () => {
    const page = await load({
        plan: { fields: [{ name: "a", label: "Age" }, { name: "b", label: "City" }] },
        form: {
            ready: false,
            fields: [
                { name: "a", widget: { el: makeElement("div"), hasError: () => false, isReady: () => false } },
                { name: "b", widget: { el: makeElement("div"), hasError: () => false, isReady: () => false } },
            ],
        },
    });

    await page.submit.click();

    assert.equal(page.message(), "Complete: Age, City");
});

test("joins the fields to fix and the fields to complete", async () => {
    const page = await load({
        plan: { fields: [{ name: "a", label: "Age" }, { name: "b", label: "City" }] },
        form: {
            ready: false,
            fields: [
                { name: "a", widget: { el: makeElement("div"), hasError: () => true, isReady: () => false } },
                { name: "b", widget: { el: makeElement("div"), hasError: () => false, isReady: () => false } },
            ],
        },
    });

    await page.submit.click();

    assert.equal(page.message(), "Fix: Age · Complete: City");
});

test("falls back to the field name when the plan carries no label", async () => {
    const page = await load({
        plan: { fields: [{ name: "a" }] },
        form: {
            ready: false,
            fields: [{
                name: "a",
                widget: { el: makeElement("div"), hasError: () => true, isReady: () => false },
            }],
        },
    });

    await page.submit.click();

    assert.equal(page.message(), "Fix: a");
});

test("disables the submit button while the request is running", async () => {
    const page = await load();

    await page.send([sse("result", { result: { type: "text", value: "x" } })]);

    assert.deepEqual(page.seen, [{ disabled: true }]);
    assert.equal(page.submit.disabled, false);
});

test("re-enables the submit button after a transport failure", async () => {
    const page = await load();

    page.response = new Error("offline");

    await page.submit.click();

    assert.equal(page.submit.disabled, false);
});

test("uploads the pending files before invoking the server", async () => {
    const completed = [];
    const page = await load({
        form: { uploads: [upload(completed, "a.txt", 10)] },
    });

    xhr.scenarios.push({ outcome: "load", status: 200, response: { uploaded: true } });

    await page.send([sse("result", { result: { type: "text", value: "x" } })]);

    assert.deepEqual(completed, ["a.txt"]);
    assert.equal(xhr.requests.length, 1);
    assert.equal(page.calls.length, 1);
});

test("does not invoke the server when an upload fails", async () => {
    const completed = [];
    const page = await load({
        form: { uploads: [upload(completed, "a.txt", 10)] },
    });

    xhr.scenarios.push({ outcome: "error" });

    await page.submit.click();

    assert.deepEqual(completed, []);
    assert.equal(page.calls.length, 0);
    assert.deepEqual(page.cards(), []);
    assert.equal(page.submit.disabled, false);
});


function kinds(page) {
    return page.posted.map((entry) => entry.data.kind);
}


function announced(page, kind) {
    return page.posted
        .filter((entry) => entry.data.kind === kind)
        .map((entry) => entry.data);
}


test("a page nobody embeds announces nothing", async () => {
    const page = await load();

    await page.send([sse("result", { result: { type: "text", value: "3" } })]);

    assert.deepEqual(page.posted, []);
});


test("an embedded page announces that it is ready", async () => {
    const page = await load({ embedded: true });

    assert.deepEqual(kinds(page), ["ready"]);
    assert.deepEqual(page.posted[0], {
        data: { v: 1, kind: "ready", slug: "add" },
        targetOrigin: "*",
    });
});


test("the slug of every message is the last segment of the path", async () => {
    const page = await load({
        embedded: true,
        pathname: "/tools/create_task/",
    });

    await page.send([sse("result", { result: { type: "text", value: "x" } })]);

    assert.deepEqual([...new Set(page.posted.map((entry) => entry.data.slug))],
                     ["create_task"]);
});


test("announces the very outputs it just drew", async () => {
    const page = await load({ embedded: true });
    const outputs = [
        { type: "text", value: "3" },
        { type: "table", headers: ["a"], rows: [["1"]] },
    ];

    const cards = await page.send([sse("result", { result: outputs })]);

    assert.deepEqual(cards, ["ftw-output-text", "ftw-output-table"]);
    assert.deepEqual(announced(page, "result"),
                     [{ v: 1, kind: "result", slug: "add", outputs }]);
});


test("announces a lone output as a list of one", async () => {
    const page = await load({ embedded: true });

    await page.send([sse("result", { result: { type: "text", value: "3" } })]);

    assert.deepEqual(announced(page, "result"), [{
        v: 1,
        kind: "result",
        slug: "add",
        outputs: [{ type: "text", value: "3" }],
    }]);
});


test("announces an empty result as an empty list", async () => {
    const page = await load({ embedded: true });

    await page.send([sse("result", { result: [] })]);

    assert.deepEqual(announced(page, "result"),
                     [{ v: 1, kind: "result", slug: "add", outputs: [] }]);
});


test("announces one result per run", async () => {
    const page = await load({ embedded: true });

    await page.send([sse("result", { result: { type: "text", value: "3" } })]);
    await page.send([sse("result", { result: { type: "text", value: "7" } })]);

    assert.deepEqual(kinds(page), ["ready", "result", "result"]);
    assert.deepEqual(announced(page, "result").map((data) => data.outputs), [
        [{ type: "text", value: "3" }],
        [{ type: "text", value: "7" }],
    ]);
});


test("announces the error the envelope carries", async () => {
    const page = await load({ embedded: true });

    await page.send([sse("result", { error: "ZeroDivisionError: division by zero" })]);

    assert.deepEqual(announced(page, "error"), [{
        v: 1,
        kind: "error",
        slug: "add",
        message: "ZeroDivisionError: division by zero",
    }]);
});


test("a field the browser rejects is not announced as an error", async () => {
    const page = await load({
        embedded: true,
        plan: { fields: [{ name: "a", label: "Age" }] },
        form: {
            ready: false,
            fields: [{
                name: "a",
                widget: {
                    el: makeElement("div"),
                    hasError: () => true,
                    isReady: () => false,
                },
            }],
        },
    });

    await page.submit.click();

    assert.equal(page.message(), "Fix: Age");
    assert.deepEqual(kinds(page), ["ready"]);
});


test("announces the navigation of an open form instead of a result", async () => {
    const page = await load({ embedded: true });

    await page.send([
        sse("result", { result: { type: "form", href: "../edit_task/?prefill=1" } }),
    ]);

    assert.deepEqual(page.assigned, ["../edit_task/?prefill=1"]);
    assert.deepEqual(kinds(page), ["ready", "navigate"]);
    assert.deepEqual(announced(page, "navigate"), [{
        v: 1,
        kind: "navigate",
        slug: "add",
        href: "../edit_task/?prefill=1",
    }]);
});


test("announces nothing when the envelope is malformed", async () => {
    const page = await load({ embedded: true });

    await page.send([sse("result", {})]);
    await page.send([
        sse("result", { result: { type: "text", value: "x" }, error: "boom" }),
    ]);

    assert.deepEqual(kinds(page), ["ready"]);
});


test("announces nothing when an output cannot be drawn", async () => {
    const page = await load({ embedded: true });

    await page.send([sse("result", { result: { type: "unknown", value: "x" } })]);

    assert.equal(page.message(), INVALID);
    assert.deepEqual(kinds(page), ["ready"]);
});


test("announces nothing when the request itself fails", async () => {
    const page = await load({ embedded: true });

    page.response = new Error("offline");

    await page.submit.click();

    assert.equal(page.message(), INVALID);
    assert.deepEqual(kinds(page), ["ready"]);
});


test("announces nothing when the stream carries no answer", async () => {
    const page = await load({ embedded: true });

    await page.send([sse("start", {})]);

    assert.equal(page.message(), INVALID);
    assert.deepEqual(kinds(page), ["ready"]);
});
