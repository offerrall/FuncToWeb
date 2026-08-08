import test from "node:test";
import assert from "node:assert/strict";

import { installDocument, makeElement, messaging, walk } from "./dom.mjs";
import { installFetch } from "./browser.mjs";
import {
    FuncToWebError, call, callStream, doc, downloadUrl, embed, events,
    fileReference, formUrl, listen, openModal, outputsOf, pageUrl, upload,
} from "../../src/func_to_web/static/sdk.js";

const FUNCTION = "/tools/add";

const SPACE = "/tools";

const TEXT = { result: { type: "text", value: "3" } };


function answer(status, payload, extra = {}) {
    return {
        ok: status >= 200 && status < 300,
        status,
        url: "http://host/tools",
        json: async () => payload,
        text: async () => JSON.stringify(payload),
        ...extra,
    };
}


function recorded(responder) {
    return installFetch((url, options) => responder(url, options));
}


function streaming(chunks) {
    const encoder = new TextEncoder();

    return answer(200, null, {
        body: {
            getReader() {
                let index = 0;

                return {
                    read: async () => (
                        index === chunks.length
                            ? { done: true, value: undefined }
                            : { done: false, value: encoder.encode(chunks[index++]) }
                    ),
                };
            },
        },
    });
}


async function refused(action) {
    try {
        await action();
    } catch (error) {
        return error;
    }

    throw new Error("the call was not refused");
}


test("call posts the arguments as a json object", async () => {
    const calls = recorded(() => answer(200, TEXT));

    await call(FUNCTION, { a: 1, b: 2 });

    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, "/tools/add/invoke");
    assert.equal(calls[0].options.method, "POST");
    assert.equal(calls[0].options.headers["Content-Type"], "application/json");
    assert.equal(calls[0].options.body, '{"a":1,"b":2}');
});


test("a trailing slash of the url is dropped", async () => {
    const calls = recorded(() => answer(200, TEXT));

    await call("/tools/add///", { a: 1 });

    assert.equal(calls[0].url, "/tools/add/invoke");
});


test("an absolute url is called as it is", async () => {
    const calls = recorded(() => answer(200, TEXT));

    await call("https://tools.example.com/add", { a: 1 });

    assert.equal(calls[0].url, "https://tools.example.com/add/invoke");
});


test("a url that is not a string is refused", async () => {
    const calls = recorded(() => answer(200, TEXT));

    assert.equal((await refused(() => call(null, { a: 1 }))).message,
                 "the url must be a string");
    assert.equal(calls.length, 0);
});


test("call resolves to the outputs of the envelope", async () => {
    recorded(() => answer(200, TEXT));

    assert.deepEqual(await call(FUNCTION, { a: 1 }),
                     [{ type: "text", value: "3" }]);
});


test("a single output is still a list", async () => {
    recorded(() => answer(200, TEXT));

    const outputs = await call(FUNCTION, { a: 1 });

    assert.equal(Array.isArray(outputs), true);
    assert.equal(outputs.length, 1);
});


test("a list of outputs keeps its order", async () => {
    recorded(() => answer(200, {
        result: [{ type: "text", value: "a" }, { type: "text", value: "b" }],
    }));

    assert.deepEqual((await call(FUNCTION, { a: 1 })).map((o) => o.value),
                     ["a", "b"]);
});


test("a call with no arguments posts an empty object", async () => {
    const calls = recorded(() => answer(200, TEXT));

    await call("/tools/report");

    assert.equal(calls[0].options.body, "{}");
});


test("an absent signal is not a reason to fail", async () => {
    const calls = recorded(() => answer(200, TEXT));

    await call(FUNCTION, { a: 1 });

    assert.equal(calls[0].options.signal, null);
});


test("the signal reaches fetch", async () => {
    const calls = recorded(() => answer(200, TEXT));
    const controller = new AbortController();

    await call(FUNCTION, { a: 1 }, { signal: controller.signal });

    assert.equal(calls[0].options.signal, controller.signal);
});


test("an error envelope becomes a FuncToWebError", async () => {
    recorded(() => answer(500, {
        error: "ZeroDivisionError: float division by zero",
    }));

    const error = await refused(() => call(FUNCTION, { a: 1 }));

    assert.equal(error instanceof FuncToWebError, true);
    assert.equal(error.name, "FuncToWebError");
    assert.equal(error.message, "ZeroDivisionError: float division by zero");
    assert.equal(error.status, 500);
    assert.equal(error.url, "/tools/add/invoke");
});


test("the envelope of the failure travels with the error", async () => {
    const payload = { error: "SchemaTypeError: a: expected int, got str" };

    recorded(() => answer(422, payload));

    const error = await refused(() => call(FUNCTION, { a: 1 }));

    assert.deepEqual(error.envelope, payload);
    assert.equal(error.status, 422);
});


test("an answer that is not an envelope carries the detail of fastapi", async () => {
    recorded(() => answer(404, { detail: "Not Found" }));

    const error = await refused(() => call(FUNCTION, { a: 1 }));

    assert.equal(error.message, "Not Found");
    assert.equal(error.status, 404);
});


test("a detail that is not text is still readable", async () => {
    recorded(() => answer(422, { detail: [{ loc: ["body"] }] }));

    const error = await refused(() => call(FUNCTION, { a: 1 }));

    assert.equal(error.message, '[{"loc":["body"]}]');
});


test("an answer that is not json is refused", async () => {
    recorded(() => answer(502, null, {
        json: async () => {
            throw new SyntaxError("not json");
        },
    }));

    const error = await refused(() => call(FUNCTION, { a: 1 }));

    assert.match(error.message, /is not an envelope \(HTTP 502\)/);
});


test("the arguments are not checked against a contract of our own", async () => {
    const calls = recorded(() => answer(422, {
        error: "SchemaTypeError: missing argument(s): a",
    }));

    const error = await refused(() => call(FUNCTION, {}));

    assert.equal(calls.length, 1);
    assert.equal(error.message, "SchemaTypeError: missing argument(s): a");
});


test("arguments that are not an object are refused", async () => {
    const calls = recorded(() => answer(200, TEXT));

    assert.equal((await refused(() => call(FUNCTION, [1, 2]))).message,
                 "the arguments must be a plain object");
    assert.equal(calls.length, 0);
});


test("a null value is a value, not an absence", async () => {
    const calls = recorded(() => answer(200, TEXT));

    await call(FUNCTION, { a: null });

    assert.equal(calls[0].options.body, '{"a":null}');
});


test("callStream reads the three events", async () => {
    const calls = recorded(() => streaming([
        'event: start\ndata: {}\n\n',
        'event: print\ndata: {"text": "one\\n"}\n\n',
        'event: print\ndata: {"text": "two\\n"}\n\n',
        'event: result\ndata: {"result": {"type": "text", "value": "3"}}\n\n',
    ]));

    const printed = [];
    let started = 0;

    const outputs = await callStream(FUNCTION, { a: 1 }, {
        onStart: () => { started += 1; },
        onPrint: (text) => printed.push(text),
    });

    assert.equal(calls[0].url, "/tools/add/invoke-stream");
    assert.equal(calls[0].options.headers.Accept, "text/event-stream");
    assert.equal(started, 1);
    assert.deepEqual(printed, ["one\n", "two\n"]);
    assert.deepEqual(outputs, [{ type: "text", value: "3" }]);
});


test("an event split across chunks is still one event", async () => {
    recorded(() => streaming([
        'event: start\ndata: {}\n\nevent: pr',
        'int\ndata: {"text": "hi\\n"}',
        '\n\nevent: result\ndata: {"result": {"type": "text", "value": "3"}}\n\n',
    ]));

    const printed = [];

    await callStream(FUNCTION, { a: 1 }, { onPrint: (text) => printed.push(text) });

    assert.deepEqual(printed, ["hi\n"]);
});


test("carriage returns of the stream are normalized", async () => {
    recorded(() => streaming([
        'event: result\r\ndata: {"result": {"type": "text", "value": "3"}}\r\n\r\n',
    ]));

    assert.deepEqual(await callStream(FUNCTION, { a: 1 }),
                     [{ type: "text", value: "3" }]);
});


test("a stream that fails carries the error of its result event", async () => {
    recorded(() => streaming([
        'event: start\ndata: {}\n\n',
        'event: result\ndata: {"error": "RuntimeError: boom"}\n\n',
    ]));

    const error = await refused(() => callStream(FUNCTION, { a: 1 }));

    assert.equal(error.message, "RuntimeError: boom");
    assert.equal(error.status, 200);
});


test("a stream cut before its result is a protocol failure", async () => {
    recorded(() => streaming(['event: start\ndata: {}\n\n']));

    assert.equal((await refused(() => callStream(FUNCTION, { a: 1 }))).message,
                 "the stream ended with no result event");
});


test("a stream refused by the host never yields an event", async () => {
    recorded(() => answer(404, { detail: "Not Found" }));

    assert.equal((await refused(() => callStream(FUNCTION, { a: 1 }))).message,
                 "Not Found");
});


test("events yields every event with its name", async () => {
    recorded(() => streaming([
        'event: start\ndata: {}\n\n',
        'event: print\ndata: {"text": "hi"}\n\n',
        'event: result\ndata: {"result": {"type": "text", "value": "3"}}\n\n',
    ]));

    const seen = [];

    for await (const event of events(FUNCTION, { a: 1 })) {
        seen.push(event.name);
    }

    assert.deepEqual(seen, ["start", "print", "result"]);
});


test("upload sends the bytes with the reference in the header", async () => {
    const calls = recorded(() => answer(200, { uploaded: true }));
    const file = new Blob(["a,b\n"]);

    const reference = await upload(SPACE, file, { reference: "data-1.csv" });

    assert.equal(reference, "data-1.csv");
    assert.equal(calls[0].url, "/tools/upload");
    assert.equal(calls[0].options.headers["X-File-Reference"], "data-1.csv");
    assert.equal(calls[0].options.headers["Content-Type"],
                 "application/octet-stream");
    assert.equal(calls[0].options.body, file);
});


test("upload mints the reference from the name of the file", async () => {
    const calls = recorded(() => answer(200, { uploaded: true }));

    const reference = await upload(SPACE, { name: "Annual Report.CSV" });

    assert.match(reference, /^annual-report-[0-9a-f-]{36}\.CSV$/);
    assert.equal(calls[0].options.headers["X-File-Reference"], reference);
});


test("an upload the server does not confirm is a failure", async () => {
    recorded(() => answer(200, { uploaded: false }));

    assert.equal((await refused(() => upload(SPACE, { name: "a.csv" }))).status,
                 200);
});


test("an upload over the size cap carries the detail of the server", async () => {
    recorded(() => answer(413, {
        detail: "uploaded file exceeds the maximum size of 10 bytes",
    }));

    const error = await refused(() => upload(SPACE, { name: "a.csv" }));

    assert.equal(error.message,
                 "uploaded file exceeds the maximum size of 10 bytes");
    assert.equal(error.status, 413);
});


test("a reference that already exists is a conflict", async () => {
    recorded(() => answer(409, {
        detail: "a file with this reference already exists",
    }));

    assert.equal((await refused(() => upload(SPACE, { name: "a.csv" }))).status,
                 409);
});


test("a file with no extension keeps its slug", () => {
    assert.match(fileReference("notes"), /^notes-[0-9a-f-]{36}$/);
});


test("a file whose name has no ascii left is only the uuid", () => {
    assert.match(fileReference("中文.csv"), /^[0-9a-f-]{36}\.csv$/);
});


test("the extension of a file is the last one", () => {
    assert.match(fileReference("archive.tar.gz"), /^archive-tar-[0-9a-f-]{36}\.gz$/);
});


test("two references of the same name differ", () => {
    assert.notEqual(fileReference("a.csv"), fileReference("a.csv"));
});


test("doc reads the contract of the space", async () => {
    const calls = recorded(() => answer(200, null, {
        text: async () => "=== Internal tools ===",
    }));

    assert.equal(await doc(SPACE), "=== Internal tools ===");
    assert.equal(calls[0].url, "/tools/doc");
});


test("a contract the host refuses is a failure", async () => {
    recorded(() => answer(404, { detail: "Not Found" }));

    assert.equal((await refused(() => doc(SPACE))).status, 404);
});


test("pageUrl builds the page of a function", () => {
    assert.equal(pageUrl(FUNCTION), "/tools/add/");
});


test("pageUrl carries prefill and hidden as json", () => {
    const url = new URL(pageUrl(FUNCTION, { prefill: { a: 9 }, hidden: ["a"] }),
                        "http://host");

    assert.equal(url.pathname, "/tools/add/");
    assert.equal(url.searchParams.get("prefill"), '{"a":9}');
    assert.equal(url.searchParams.get("hidden"), '["a"]');
});


test("pageUrl asks for an autorun only when told to", () => {
    assert.equal(pageUrl(FUNCTION), "/tools/add/");
    assert.equal(pageUrl(FUNCTION, { autorun: false }), "/tools/add/");
    assert.equal(pageUrl(FUNCTION, { autorun: true }), "/tools/add/?autorun=1");
});


test("pageUrl carries autorun beside prefill and hidden", () => {
    const url = new URL(
        pageUrl(FUNCTION, { prefill: { a: 9 }, hidden: ["a"], autorun: true }),
        "http://host");

    assert.equal(url.pathname, "/tools/add/");
    assert.equal(url.searchParams.get("prefill"), '{"a":9}');
    assert.equal(url.searchParams.get("hidden"), '["a"]');
    assert.equal(url.searchParams.get("autorun"), "1");
});


test("embed passes autorun through to the page it mounts", () => {
    const document = installDocument();
    const panel = makeElement("div", { id: "panel" });

    document.body.append(panel);

    const frame = embed(panel, FUNCTION, { prefill: { a: 9 }, autorun: true });

    assert.equal(new URL(frame.src, "http://host").searchParams.get("autorun"),
                 "1");
});


test("openModal passes autorun through to the page it opens", () => {
    installDocument();

    const modal = openModal(FUNCTION, { autorun: true, prefill: { a: 9 } });
    const query = new URL(modal.iframe.src, "http://host").searchParams;

    assert.equal(query.get("autorun"), "1");
    assert.equal(query.get("prefill"), '{"a":9}');
});


test("openModal opens a plain page when nothing asks for an autorun", () => {
    installDocument();

    assert.equal(openModal(FUNCTION).iframe.src, "/tools/add/");
});


test("downloadUrl escapes the reference", () => {
    assert.equal(downloadUrl(SPACE, "a b.csv"), "/tools/returns/a%20b.csv");
});


test("formUrl resolves the relative href of a form output", () => {
    assert.equal(formUrl(SPACE, { href: "../add/?prefill=%7B%7D" }),
                 "/tools/add/?prefill=%7B%7D");
});


test("formUrl leaves an href that is not relative alone", () => {
    assert.equal(formUrl(SPACE, { href: "http://other/add/" }),
                 "http://other/add/");
});


test("outputsOf refuses an envelope that carries both keys", () => {
    assert.throws(() => outputsOf({ result: 1, error: "x" }), FuncToWebError);
});


test("outputsOf refuses an envelope that carries neither", () => {
    assert.throws(() => outputsOf({}), FuncToWebError);
});


test("outputsOf refuses something that is not an object", () => {
    assert.throws(() => outputsOf([1, 2]), FuncToWebError);
    assert.throws(() => outputsOf(null), FuncToWebError);
});


test("embed puts the page of a function inside the element", () => {
    const document = installDocument();
    const panel = makeElement("div", { id: "panel" });

    document.body.append(panel);

    const frame = embed(panel, FUNCTION, { prefill: { a: 9 } });

    assert.equal(frame.tagName, "IFRAME");
    assert.equal(frame.parent, panel);
    assert.equal(frame.className, "ftw-frame");
    assert.match(frame.src, /^\/tools\/add\/\?prefill=/);
});


test("embed accepts a selector instead of an element", () => {
    const document = installDocument();

    document.body.append(makeElement("div", { className: "slot" }));

    const frame = embed(".slot", FUNCTION);

    assert.equal(frame.parent.className, "slot");
    assert.equal(frame.src, "/tools/add/");
});


test("embed refuses a selector that matches nothing", () => {
    installDocument();

    assert.throws(() => embed("#nowhere", FUNCTION), FuncToWebError);
});


test("embed injects its style sheet once", () => {
    const document = installDocument();

    document.body.append(makeElement("div", { className: "slot" }));

    embed(".slot", FUNCTION);
    embed(".slot", FUNCTION);

    const styles = walk(document.head).filter((n) => n.tagName === "STYLE");

    assert.equal(styles.length, 1);
    assert.match(styles[0].textContent, /\.ftw-frame/);
});


test("openModal puts the page in an overlay of the body", () => {
    const document = installDocument();

    const modal = openModal(FUNCTION, { prefill: { a: 9 } });

    assert.equal(modal.element.parent, document.body);
    assert.equal(modal.element.className, "ftw-modal");
    assert.equal(modal.iframe.tagName, "IFRAME");
    assert.match(modal.iframe.src, /^\/tools\/add\/\?prefill=/);
});


test("the modal is tall by default so a form is not cut off", () => {
    installDocument();

    openModal(FUNCTION);

    const sheet = document.getElementById("functoweb-modal-style").textContent;

    assert.match(sheet, /--ftw-modal-height,\s*90vh/);
    assert.match(sheet, /--ftw-modal-width,\s*760px/);
});


test("the sheet keeps every size inside the window", () => {
    installDocument();

    openModal(FUNCTION);

    const sheet = document.getElementById("functoweb-modal-style").textContent;

    assert.match(sheet, /width:\s*min\(var\(--ftw-modal-width[^)]*\),\s*100%\)/);
    assert.match(sheet, /height:\s*min\(var\(--ftw-modal-height[^)]*\),\s*100%\)/);
});


test("a modal given no size sets no property of its own", () => {
    installDocument();

    const modal = openModal(FUNCTION);

    assert.deepEqual(modal.element.children[0].style.properties, {});
});


test("openModal takes a size in pixels as a number", () => {
    installDocument();

    const modal = openModal(FUNCTION, { width: 1200, height: 900 });
    const panel = modal.element.children[0];

    assert.equal(panel.style.getPropertyValue("--ftw-modal-width"), "1200px");
    assert.equal(panel.style.getPropertyValue("--ftw-modal-height"), "900px");
});


test("openModal takes any css length as a string", () => {
    installDocument();

    const panels = [
        ["80vh", "80vh"],
        ["100%", "100%"],
        ["48rem", "48rem"],
        ["  70vh  ", "70vh"],
        ["calc(100% - 4rem)", "calc(100% - 4rem)"],
    ].map(([given, want]) => {
        const modal = openModal(FUNCTION, { height: given });

        return [modal.element.children[0]
            .style.getPropertyValue("--ftw-modal-height"), want];
    });

    for (const [got, want] of panels) assert.equal(got, want);
});


test("openModal sizes one axis without touching the other", () => {
    installDocument();

    const panel = openModal(FUNCTION, { height: "95vh" }).element.children[0];

    assert.equal(panel.style.getPropertyValue("--ftw-modal-height"), "95vh");
    assert.equal(panel.style.getPropertyValue("--ftw-modal-width"), "");
});


test("openModal refuses a size that is not a length", () => {
    installDocument();

    for (const value of [true, {}, [], "", "   ", Number.NaN, Infinity]) {
        assert.throws(() => openModal(FUNCTION, { height: value }),
                      /must be a number of pixels or a CSS length/);
    }
});


test("the size is not sent to the page as a query parameter", () => {
    installDocument();

    const modal = openModal(FUNCTION, { width: 1200, height: 900 });

    assert.equal(modal.iframe.src, "/tools/add/");
});


test("the close button of the modal removes it", () => {
    const document = installDocument();
    const closed = [];

    const modal = openModal(FUNCTION, { onClose: () => closed.push(true) });
    const button = walk(modal.element).find((n) => n.tagName === "BUTTON");

    button.click();

    assert.deepEqual(document.body.children, []);
    assert.deepEqual(closed, [true]);
});


test("a click outside the panel closes the modal", () => {
    const document = installDocument();
    const modal = openModal(FUNCTION);

    modal.element.dispatch("click", { target: modal.element });

    assert.deepEqual(document.body.children, []);
});


test("a click inside the panel leaves the modal open", () => {
    const document = installDocument();
    const modal = openModal(FUNCTION);

    modal.element.dispatch("click", { target: modal.iframe });

    assert.deepEqual(document.body.children, [modal.element]);
});


test("escape closes the modal and stops listening", () => {
    const document = installDocument();
    const modal = openModal(FUNCTION);

    document.dispatch("keydown", { key: "Escape" });

    assert.deepEqual(document.body.children, []);
    assert.equal(document.listeners.get("keydown").size, 0);

    modal.close();
});


test("a key that is not escape leaves the modal open", () => {
    const document = installDocument();
    const modal = openModal(FUNCTION);

    document.dispatch("keydown", { key: "Enter" });

    assert.deepEqual(document.body.children, [modal.element]);
});


test("closing a modal twice notifies once", () => {
    installDocument();

    const closed = [];
    const modal = openModal(FUNCTION, { onClose: () => closed.push(true) });

    modal.close();
    modal.close();

    assert.deepEqual(closed, [true]);
});


const PENDING = Symbol("pending");

const OUTPUTS = [{ type: "text", value: "3" }];

const OTHER = [{ type: "text", value: "7" }];


function message(kind, extra = {}) {
    return { v: 1, kind, slug: "add", ...extra };
}


function opened(options = {}) {
    const document = installDocument();
    const bus = messaging();
    const modal = openModal(FUNCTION, options);

    modal.iframe.contentWindow = { name: "inner" };

    return { document, bus, modal };
}


function announce(bus, modal, data) {
    bus.send(modal.iframe.contentWindow, data);
}


function state(promise) {
    return Promise.race([promise, Promise.resolve(PENDING)]);
}


test("listen ignores a message coming from another frame", () => {
    installDocument();

    const bus = messaging();
    const frame = makeElement("iframe");
    const seen = [];

    frame.contentWindow = { name: "mine" };

    listen(frame, { onResult: (outputs) => seen.push(outputs) });

    bus.send({ name: "someone else" }, message("result", { outputs: OUTPUTS }));

    assert.deepEqual(seen, []);
});


test("listen ignores a message while the frame has no window", () => {
    installDocument();

    const bus = messaging();
    const frame = makeElement("iframe");
    const seen = [];

    listen(frame, { onResult: (outputs) => seen.push(outputs) });

    bus.send(undefined, message("result", { outputs: OUTPUTS }));

    assert.deepEqual(seen, []);
});


test("listen ignores everything foreign to the protocol", () => {
    installDocument();

    const bus = messaging();
    const frame = makeElement("iframe");
    const seen = [];

    frame.contentWindow = { name: "inner" };

    const channel = listen(frame, {
        onReady: () => seen.push("ready"),
        onResult: (outputs) => seen.push(outputs),
        onError: (text) => seen.push(text),
        onNavigate: (href) => seen.push(href),
    });

    const foreign = [
        null,
        "a string",
        42,
        { kind: "result", outputs: OUTPUTS },
        { v: 2, kind: "result", outputs: OUTPUTS },
        { v: "1", kind: "result", outputs: OUTPUTS },
        { v: 1, outputs: OUTPUTS },
        { v: 1, kind: 7 },
        { v: 1, kind: "whatever" },
        { v: 1, kind: "result" },
        { v: 1, kind: "result", outputs: "not an array" },
    ];

    for (const data of foreign) bus.send(frame.contentWindow, data);

    assert.deepEqual(seen, []);
    assert.deepEqual(channel.cache, { ready: false, results: null, error: null });
});


test("listen caches the last result and the last error", () => {
    installDocument();

    const bus = messaging();
    const frame = makeElement("iframe");

    frame.contentWindow = { name: "inner" };

    const channel = listen(frame);

    bus.send(frame.contentWindow, message("ready"));
    bus.send(frame.contentWindow, message("result", { outputs: OUTPUTS }));
    bus.send(frame.contentWindow, message("result", { outputs: OTHER }));
    bus.send(frame.contentWindow, message("error", { message: "boom" }));

    assert.equal(channel.cache.ready, true);
    assert.deepEqual(channel.cache.results, OTHER);
    assert.equal(channel.cache.error, "boom");
});


test("listen reports every kind to its handler", () => {
    installDocument();

    const bus = messaging();
    const frame = makeElement("iframe");
    const seen = [];

    frame.contentWindow = { name: "inner" };

    listen(frame, {
        onReady: () => seen.push(["ready"]),
        onResult: (outputs) => seen.push(["result", outputs]),
        onError: (text) => seen.push(["error", text]),
        onNavigate: (href) => seen.push(["navigate", href]),
    });

    bus.send(frame.contentWindow, message("ready"));
    bus.send(frame.contentWindow, message("result", { outputs: OUTPUTS }));
    bus.send(frame.contentWindow, message("error", { message: "boom" }));
    bus.send(frame.contentWindow, message("navigate", { href: "../edit_task/" }));

    assert.deepEqual(seen, [
        ["ready"],
        ["result", OUTPUTS],
        ["error", "boom"],
        ["navigate", "../edit_task/"],
    ]);
});


test("listen works with no handlers at all", () => {
    installDocument();

    const bus = messaging();
    const frame = makeElement("iframe");

    frame.contentWindow = { name: "inner" };

    const channel = listen(frame);

    bus.send(frame.contentWindow, message("navigate", { href: "../x/" }));
    bus.send(frame.contentWindow, message("result", { outputs: OUTPUTS }));

    assert.deepEqual(channel.cache.results, OUTPUTS);
});


test("stop leaves the channel deaf", () => {
    installDocument();

    const bus = messaging();
    const frame = makeElement("iframe");
    const seen = [];

    frame.contentWindow = { name: "inner" };

    const channel = listen(frame, { onResult: (outputs) => seen.push(outputs) });

    assert.equal(bus.count(), 1);

    channel.stop();

    assert.equal(bus.count(), 0);

    bus.send(frame.contentWindow, message("result", { outputs: OUTPUTS }));

    assert.deepEqual(seen, []);
    assert.equal(channel.cache.results, null);
});


test("the modal handle keeps its three original members and adds closed", () => {
    const { document, modal } = opened();

    assert.equal(modal.element.parent, document.body);
    assert.equal(modal.iframe.tagName, "IFRAME");
    assert.equal(typeof modal.close, "function");
    assert.ok(modal.closed instanceof Promise);
});


test("closed resolves with nothing completed when the modal never ran", async () => {
    const { modal } = opened();

    modal.close();

    assert.deepEqual(await modal.closed, { completed: false, results: null });
});


test("closed carries the last of two results", async () => {
    const { bus, modal } = opened();

    announce(bus, modal, message("result", { outputs: OUTPUTS }));
    announce(bus, modal, message("result", { outputs: OTHER }));

    modal.close();

    assert.deepEqual(await modal.closed, { completed: true, results: OTHER });
});


test("an error alone does not make the session completed", async () => {
    const { bus, modal } = opened();

    announce(bus, modal, message("error", { message: "boom" }));

    modal.close();

    assert.deepEqual(await modal.closed, { completed: false, results: null });
});


test("closeOnResult closes the modal on the first result", async () => {
    const { document, bus, modal } = opened({ closeOnResult: true });

    announce(bus, modal, message("result", { outputs: OUTPUTS }));

    assert.deepEqual(document.body.children, []);
    assert.deepEqual(await modal.closed, { completed: true, results: OUTPUTS });
});


test("a result leaves the modal open by default", async () => {
    const { document, bus, modal } = opened();

    announce(bus, modal, message("result", { outputs: OUTPUTS }));

    assert.deepEqual(document.body.children, [modal.element]);
    assert.equal(await state(modal.closed), PENDING);
});


test("the modal reports the result and the error to its own handlers", () => {
    const seen = [];
    const { bus, modal } = opened({
        onResult: (outputs) => seen.push(["result", outputs]),
        onError: (text) => seen.push(["error", text]),
    });

    announce(bus, modal, message("result", { outputs: OUTPUTS }));
    announce(bus, modal, message("error", { message: "boom" }));

    assert.deepEqual(seen, [["result", OUTPUTS], ["error", "boom"]]);
});


test("escape resolves closed as any other way out", async () => {
    const { document, bus, modal } = opened();

    announce(bus, modal, message("result", { outputs: OUTPUTS }));
    document.dispatch("keydown", { key: "Escape" });

    assert.deepEqual(await modal.closed, { completed: true, results: OUTPUTS });
});


test("the close button resolves closed", async () => {
    const { modal } = opened();
    const button = walk(modal.element).find((n) => n.tagName === "BUTTON");

    button.click();

    assert.deepEqual(await modal.closed, { completed: false, results: null });
});


test("a click on the backdrop resolves closed", async () => {
    const { modal } = opened();

    modal.element.dispatch("click", { target: modal.element });

    assert.deepEqual(await modal.closed, { completed: false, results: null });
});


test("closed resolves exactly once when the close fires twice", async () => {
    const { modal } = opened();
    const settled = [];

    modal.closed.then((value) => settled.push(value));

    modal.close();
    modal.close();

    await modal.closed;
    await Promise.resolve();

    assert.deepEqual(settled, [{ completed: false, results: null }]);
});


test("a modal stops listening once it is closed", async () => {
    const { bus, modal } = opened();

    modal.close();

    assert.equal(bus.count(), 0);

    announce(bus, modal, message("result", { outputs: OUTPUTS }));

    assert.deepEqual(await modal.closed, { completed: false, results: null });
});


test("a url that will not load still returns a usable handle", async () => {
    const document = installDocument();

    const modal = openModal("/tools/nope");

    assert.notEqual(modal, undefined);
    assert.ok(modal.closed instanceof Promise);
    assert.equal(modal.element.parent, document.body);
    assert.match(modal.iframe.src, /^\/tools\/nope\/$/);

    modal.close();

    assert.deepEqual(await modal.closed, { completed: false, results: null });
});


test("a modal closed before its frame loads resolves anyway", async () => {
    installDocument();

    const modal = openModal(FUNCTION);

    assert.equal(modal.iframe.contentWindow, undefined);

    modal.close();

    assert.deepEqual(await modal.closed, { completed: false, results: null });
});


test("navigate does not count as a result", async () => {
    const seen = [];
    const { bus, modal } = opened({ closeOnResult: true });

    listen(modal.iframe, { onNavigate: (href) => seen.push(href) });

    announce(bus, modal, message("navigate", { href: "../edit_task/?prefill=1" }));

    modal.close();

    assert.deepEqual(seen, ["../edit_task/?prefill=1"]);
    assert.deepEqual(await modal.closed, { completed: false, results: null });
});
