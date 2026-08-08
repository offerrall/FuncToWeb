import test from "node:test";
import assert from "node:assert/strict";

import { installDocument, find, only, tagsIn, walk } from "./dom.mjs";
import {
    installClipboard, installObjectUrls, installTimers, installFetch,
} from "./browser.mjs";

const XSS = "<script>alert(1)</script>";
const SVG_TAGS = new Set([
    "SVG", "PATH", "CIRCLE", "G", "USE", "RECT", "LINE", "POLYLINE", "POLYGON",
]);

let document = installDocument();
let clipboard = installClipboard();
let objectUrls = installObjectUrls();
let timers = installTimers();
let fetches = installFetch(async () => ({
    async blob() {
        return new Blob(["image-bytes"], { type: "image/png" });
    },
}));

const {
    renderText, renderError, renderRunning, renderStdout, renderTable,
    renderDownload, renderForm, renderImage,
} = await import("../../src/func_to_web/static/output.js");

test.beforeEach(() => {
    document = installDocument();
    clipboard = installClipboard();
    objectUrls = installObjectUrls();
    timers = installTimers();
    fetches = installFetch(async () => ({
        async blob() {
            return new Blob(["image-bytes"], { type: "image/png" });
        },
    }));
});

function classes(element) {
    return [...element.classes()].sort();
}

function anchors() {
    return document.created.filter((element) => element.tagName === "A");
}

function table() {
    return {
        headers: ["name", "value"],
        rows: [["a", "1"], ["b", "2"], ["c", "3"]],
        type: "table",
    };
}


test("renderText builds a text output card with a value and one action", () => {
    const element = renderText({ type: "text", value: "hello" });

    assert.equal(element.tagName, "DIV");
    assert.deepEqual(classes(element), ["ftw-output", "ftw-output-text"]);

    const value = only(element, ".ftw-output-value");

    assert.equal(value.tagName, "PRE");
    assert.equal(value.textContent, "hello");

    assert.equal(find(element, ".ftw-actions").length, 1);
    assert.equal(find(element, ".ftw-action").length, 1);
});

test("renderText marks the card with a check icon", () => {
    const element = renderText({ type: "text", value: "hello" });
    const mark = only(element, ".ftw-output-mark");

    assert.equal(mark.tagName, "SPAN");
    assert.ok(mark.classes().has("ftw-icon-check"));
});

test("renderText inserts the value as text and never as markup", () => {
    const element = renderText({ type: "text", value: XSS });

    assert.equal(only(element, ".ftw-output-value").textContent, XSS);
    assert.ok(!tagsIn(element).includes("SCRIPT"));
});

test("renderText copies the exact value to the clipboard", async () => {
    const element = renderText({ type: "text", value: XSS });

    await only(element, ".ftw-action").click();

    assert.deepEqual(clipboard.texts, [XSS]);
});

test("renderText copy button confirms and then restores its icon", async () => {
    const element = renderText({ type: "text", value: "hello" });
    const button = only(element, ".ftw-action");

    await button.click();

    assert.ok(button.classList.contains("done"));
    assert.ok(button.children[0].classes().has("ftw-icon-check"));

    timers.flush();

    assert.ok(!button.classList.contains("done"));
    assert.ok(button.children[0].classes().has("ftw-icon-copy"));
});

test("renderText copy button does not confirm when copying fails", async () => {
    Object.defineProperty(globalThis, "navigator", {
        value: {
            clipboard: {
                writeText: async () => {
                    throw new Error("denied");
                },
            },
        },
        writable: true,
        configurable: true,
    });

    const element = renderText({ type: "text", value: "hello" });
    const button = only(element, ".ftw-action");

    await button.click();

    assert.ok(!button.classList.contains("done"));
    assert.equal(timers.pending.length, 0);
});

test("renderError builds an error card with an alert icon and no actions", () => {
    const element = renderError("boom");

    assert.deepEqual(classes(element), ["ftw-output", "ftw-output-error"]);
    assert.equal(only(element, ".ftw-output-value").textContent, "boom");
    assert.ok(only(element, ".ftw-output-mark").classes().has("ftw-icon-alert"));
    assert.equal(find(element, ".ftw-actions").length, 0);
});

test("renderError inserts the message as text and never as markup", () => {
    const element = renderError(XSS);

    assert.equal(only(element, ".ftw-output-value").textContent, XSS);
    assert.ok(!tagsIn(element).includes("SCRIPT"));
});

test("renderRunning builds a running card with a clock icon", () => {
    const element = renderRunning();

    assert.deepEqual(classes(element), ["ftw-output", "ftw-output-running"]);
    assert.equal(only(element, ".ftw-output-value").textContent, "Running…");
    assert.ok(only(element, ".ftw-output-mark").classes().has("ftw-icon-clock"));
});

test("renderStdout returns an element and an append function", () => {
    const stdout = renderStdout();

    assert.equal(typeof stdout.append, "function");
    assert.deepEqual(classes(stdout.element), ["ftw-output", "ftw-output-stdout"]);
    assert.equal(only(stdout.element, ".ftw-output-value").textContent, "");
});

test("renderStdout append accumulates every chunk in a single pre", () => {
    const stdout = renderStdout();
    const before = stdout.element.children.length;

    stdout.append("one\n");
    stdout.append("two\n");
    stdout.append("three");

    const values = find(stdout.element, ".ftw-output-value");

    assert.equal(values.length, 1);
    assert.equal(values[0].tagName, "PRE");
    assert.equal(values[0].textContent, "one\ntwo\nthree");
    assert.equal(stdout.element.children.length, before);
});

test("renderStdout never creates one card per chunk", () => {
    const stdout = renderStdout();

    for (let index = 0; index < 20; index += 1) stdout.append(`${index}`);

    assert.equal(walk(stdout.element).length, 3);
    assert.equal(find(stdout.element, ".ftw-output").length, 1);
});

test("renderStdout appends chunks as text and never as markup", () => {
    const stdout = renderStdout();

    stdout.append(XSS);

    assert.equal(only(stdout.element, ".ftw-output-value").textContent, XSS);
    assert.ok(!tagsIn(stdout.element).includes("SCRIPT"));
});

// A function printing in a loop: the page keeps the tail, follows it, and
// stops following whoever scrolled up to read.

function lines(count, from = 0) {
    let text = "";

    for (let index = from; index < from + count; index += 1) {
        text += `line ${index}\n`;
    }

    return text;
}

// A reader moving the box, as a browser reports it: the position changes and
// a scroll event follows.
function scrolledTo(element, { height, visible, top }) {
    element.scrollHeight = height;
    element.clientHeight = visible;
    element.scrollTop = top;
    element.dispatch("scroll");
}

test("renderStdout keeps a long run under a bounded amount of text", () => {
    const stdout = renderStdout();
    const value = only(stdout.element, ".ftw-output-value");

    for (let round = 0; round < 40; round += 1) {
        stdout.append(lines(1000, round * 1000));
    }

    assert.ok(value.textContent.length < 60000, `${value.textContent.length}`);
});

test("renderStdout keeps the end of what was printed, not the start", () => {
    const stdout = renderStdout();
    const value = only(stdout.element, ".ftw-output-value");

    stdout.append(lines(20000));

    assert.ok(value.textContent.endsWith("line 19999\n"));
    assert.ok(!value.textContent.includes("line 0\n"));
});

test("renderStdout says so when it has dropped anything", () => {
    const stdout = renderStdout();
    const value = only(stdout.element, ".ftw-output-value");

    stdout.append(lines(20000));

    assert.ok(value.textContent.startsWith("… earlier output trimmed\n"));
});

test("renderStdout drops nothing, and says nothing, on a short run", () => {
    const stdout = renderStdout();
    const value = only(stdout.element, ".ftw-output-value");

    stdout.append(lines(100));

    assert.equal(value.textContent, lines(100));
});

test("renderStdout cuts on a line break, never mid-line", () => {
    const stdout = renderStdout();
    const value = only(stdout.element, ".ftw-output-value");

    stdout.append(lines(20000));

    const kept = value.textContent.slice("… earlier output trimmed\n".length);

    assert.ok(/^line \d+\n/.test(kept), kept.slice(0, 40));
});

test("renderStdout follows the bottom while it is being followed", () => {
    const stdout = renderStdout();
    const value = only(stdout.element, ".ftw-output-value");

    scrolledTo(value, { height: 1000, visible: 200, top: 800 });
    stdout.append("one more\n");

    assert.equal(value.scrollTop, 1000);
});

test("renderStdout leaves a reader who scrolled up where they are", () => {
    const stdout = renderStdout();
    const value = only(stdout.element, ".ftw-output-value");

    scrolledTo(value, { height: 1000, visible: 200, top: 120 });
    stdout.append("one more\n");

    assert.equal(value.scrollTop, 120);
});

test("renderStdout follows again once the reader returns to the bottom", () => {
    const stdout = renderStdout();
    const value = only(stdout.element, ".ftw-output-value");

    scrolledTo(value, { height: 1000, visible: 200, top: 120 });
    stdout.append("while away\n");

    assert.equal(value.scrollTop, 120);

    scrolledTo(value, { height: 1400, visible: 200, top: 1200 });
    stdout.append("back at the bottom\n");

    assert.equal(value.scrollTop, 1400);
});

test("renderStdout counts a few pixels short of the bottom as the bottom", () => {
    const stdout = renderStdout();
    const value = only(stdout.element, ".ftw-output-value");

    // What a browser reports for a box that is at the bottom: the three
    // fractions rarely cancel out exactly.
    scrolledTo(value, { height: 1000, visible: 200, top: 797 });
    stdout.append("one more\n");

    assert.equal(value.scrollTop, 1000);
});

test("renderStdout follow puts the view back at the end after a remount", () => {
    const stdout = renderStdout();
    const value = only(stdout.element, ".ftw-output-value");

    stdout.append(lines(50));

    // What replaceChildren() does to it: a node taken out of the document
    // and put back comes back at the top, with everything else intact.
    value.scrollHeight = 900;
    value.clientHeight = 200;
    value.scrollTop = 0;

    stdout.follow();

    assert.equal(value.scrollTop, 900);
});

test("renderStdout follow leaves a reader who scrolled up alone", () => {
    const stdout = renderStdout();
    const value = only(stdout.element, ".ftw-output-value");

    stdout.append(lines(50));
    scrolledTo(value, { height: 1000, visible: 200, top: 100 });

    stdout.follow();

    assert.equal(value.scrollTop, 100);
});

test("renderStdout follows an element that has no layout at all", () => {
    const stdout = renderStdout();
    const value = only(stdout.element, ".ftw-output-value");

    value.scrollHeight = undefined;
    value.clientHeight = undefined;

    stdout.append("printed before any layout\n");

    assert.equal(value.scrollTop, undefined);
    assert.equal(value.textContent, "printed before any layout\n");
});

test("renderTable builds a thead and a tbody with the right shape", () => {
    const element = renderTable(table());

    assert.deepEqual(classes(element), ["ftw-output", "ftw-output-table"]);

    const head = only(element, "thead");
    const body = only(element, "tbody");

    assert.equal(head.children.length, 1);
    assert.equal(head.children[0].tagName, "TR");
    assert.equal(head.children[0].children.length, 2);
    assert.deepEqual(head.children[0].children.map((cell) => cell.tagName),
                     ["TH", "TH"]);

    assert.equal(body.children.length, 3);

    for (const line of body.children) {
        assert.equal(line.tagName, "TR");
        assert.equal(line.children.length, 2);
        assert.deepEqual(line.children.map((cell) => cell.tagName), ["TD", "TD"]);
    }
});

test("renderTable fills header and body cells with text", () => {
    const element = renderTable(table());

    assert.deepEqual(find(element, "th").map((cell) => cell.textContent),
                     ["name", "value"]);
    assert.deepEqual(find(element, "td").map((cell) => cell.textContent),
                     ["a", "1", "b", "2", "c", "3"]);
});

test("renderTable supports a table with no rows", () => {
    const element = renderTable({ headers: ["only"], rows: [] });

    assert.equal(only(element, "thead").children.length, 1);
    assert.equal(only(element, "tbody").children.length, 0);
});

test("renderTable inserts cell text and never markup", () => {
    const element = renderTable({ headers: [XSS], rows: [[XSS]] });

    assert.equal(only(element, "th").textContent, XSS);
    assert.equal(only(element, "td").textContent, XSS);
    assert.ok(!tagsIn(element).includes("SCRIPT"));
});

test("renderTable wraps the table in a scrollable grid", () => {
    const element = renderTable(table());
    const grid = only(element, ".ftw-output-grid");

    assert.equal(grid.children.length, 1);
    assert.equal(grid.children[0].tagName, "TABLE");
});

test("renderTable copies the table as tab separated text", async () => {
    const element = renderTable(table());

    await find(element, ".ftw-action")[0].click();

    assert.deepEqual(clipboard.texts,
                     ["name\tvalue\na\t1\nb\t2\nc\t3"]);
});

test("renderTable copies cells containing quotes and commas verbatim", async () => {
    const element = renderTable({
        headers: ["a", "b,c"],
        rows: [['say "hi"', "plain"]],
    });

    await find(element, ".ftw-action")[0].click();

    assert.deepEqual(clipboard.texts, ['a\tb,c\nsay "hi"\tplain']);
});

test("renderTable downloads a csv that quotes commas and doubles quotes",
     async () => {
    const element = renderTable({
        headers: ["a", "b,c"],
        rows: [['say "hi"', "plain"], ["line1\nline2", "x"]],
    });

    await find(element, ".ftw-action")[1].click();

    assert.equal(objectUrls.created.length, 1);

    const csv = await objectUrls.created[0].blob.text();

    assert.equal(
        csv,
        'a,"b,c"\r\n"say ""hi""",plain\r\n"line1\nline2",x');
});

test("renderTable csv leaves plain cells unquoted", async () => {
    const element = renderTable(table());

    await find(element, ".ftw-action")[1].click();

    const csv = await objectUrls.created[0].blob.text();

    assert.equal(csv, "name,value\r\na,1\r\nb,2\r\nc,3");
});

test("renderTable csv quotes cells containing a carriage return", async () => {
    const element = renderTable({ headers: ["h"], rows: [["a\rb"]] });

    await find(element, ".ftw-action")[1].click();

    const csv = await objectUrls.created[0].blob.text();

    assert.equal(csv, 'h\r\n"a\rb"');
});

test("renderTable csv download uses a csv media type and filename", async () => {
    const element = renderTable(table());

    await find(element, ".ftw-action")[1].click();

    assert.equal(objectUrls.created[0].blob.type, "text/csv;charset=utf-8");

    const link = anchors().at(-1);

    assert.equal(link.href, objectUrls.created[0].source);
    assert.equal(link.download, "table.csv");
    assert.equal(link.clicks, 1);
});

test("renderTable csv download revokes the object url later", async () => {
    const element = renderTable(table());

    await find(element, ".ftw-action")[1].click();

    assert.deepEqual(timers.pending.map((entry) => entry.delay), [10000]);
    assert.deepEqual(objectUrls.revoked, []);

    timers.flush();

    assert.deepEqual(objectUrls.revoked, [objectUrls.created[0].source]);
});

test("renderTable download button does not swap to a confirmation icon",
     async () => {
    const element = renderTable(table());
    const button = find(element, ".ftw-action")[1];

    await button.click();

    assert.ok(!button.classList.contains("done"));
    assert.ok(button.children[0].classes().has("ftw-icon-download"));
});

test("renderDownload builds a relative href under ../returns", () => {
    const element = renderDownload({
        type: "download", value: "abc123", filename: "report.pdf",
    });

    assert.deepEqual(classes(element), ["ftw-output", "ftw-output-download"]);

    const link = only(element, ".ftw-download");

    assert.equal(link.tagName, "A");
    assert.equal(link.href, "../returns/abc123");
    assert.equal(link.download, "report.pdf");
});

test("renderDownload percent encodes the reference", () => {
    const element = renderDownload({
        type: "download", value: "a/b c?d#e&f", filename: "x.txt",
    });

    assert.equal(only(element, ".ftw-download").href,
                 "../returns/a%2Fb%20c%3Fd%23e%26f");
});

test("renderDownload never lets a reference escape the returns path", () => {
    const element = renderDownload({
        type: "download", value: "../../etc/passwd", filename: "x.txt",
    });

    assert.equal(only(element, ".ftw-download").href,
                 "../returns/..%2F..%2Fetc%2Fpasswd");
});

test("renderDownload shows the filename as text", () => {
    const element = renderDownload({
        type: "download", value: "ref", filename: XSS,
    });

    const name = only(element, ".ftw-download").children[1];

    assert.equal(name.tagName, "SPAN");
    assert.equal(name.textContent, XSS);
    assert.ok(!tagsIn(element).includes("SCRIPT"));
});

test("renderDownload puts a download icon before the filename", () => {
    const element = renderDownload({
        type: "download", value: "ref", filename: "x.txt",
    });

    const icon = only(element, ".ftw-download").children[0];

    assert.ok(icon.classes().has("ftw-icon-download"));
});

test("renderForm uses the href exactly as given", () => {
    const element = renderForm({ type: "form", href: "../step-two?a=1&b=2" });

    assert.deepEqual(classes(element), ["ftw-output", "ftw-output-form"]);

    const link = only(element, ".ftw-download");

    assert.equal(link.tagName, "A");
    assert.equal(link.href, "../step-two?a=1&b=2");
});

test("renderForm does not encode or rewrite the href", () => {
    const href = "../other/form?value=a%20b&next=/x";
    const element = renderForm({ type: "form", href });

    assert.equal(only(element, ".ftw-download").href, href);
});

test("renderForm shows a waiting label and a clock icon", () => {
    const element = renderForm({ type: "form", href: "../next" });
    const link = only(element, ".ftw-download");

    assert.ok(link.children[0].classes().has("ftw-icon-clock"));
    assert.equal(link.children[1].textContent, "Opening the form…");
});

test("renderImage sets the source and an empty alt", () => {
    const element = renderImage({ type: "image", value: "data:image/png;base64,AA" });

    assert.deepEqual(classes(element), ["ftw-output", "ftw-output-image"]);

    const image = only(element, ".ftw-output-img");

    assert.equal(image.tagName, "IMG");
    assert.equal(image.src, "data:image/png;base64,AA");
    assert.equal(image.alt, "");
});

test("renderImage offers a copy and a download action", () => {
    const element = renderImage({ type: "image", value: "img.png" });

    assert.equal(find(element, ".ftw-action").length, 2);
});

test("renderImage copies the image through the clipboard api", async () => {
    const element = renderImage({ type: "image", value: "img.png" });

    await find(element, ".ftw-action")[0].click();

    assert.deepEqual(fetches.map((call) => call.url), ["img.png"]);
    assert.equal(clipboard.items.length, 1);
    assert.deepEqual(Object.keys(clipboard.items[0][0].payload), ["image/png"]);
});

test("renderImage downloads the source under a png filename", async () => {
    const element = renderImage({ type: "image", value: "img.png" });
    const button = find(element, ".ftw-action")[1];

    await button.click();

    const link = anchors().at(-1);

    assert.equal(link.href, "img.png");
    assert.equal(link.download, "image.png");
    assert.equal(link.clicks, 1);
    assert.ok(!button.classList.contains("done"));
});

test("every icon is an aria hidden span with a ftw-icon class", () => {
    const elements = [
        renderText({ type: "text", value: "x" }),
        renderError("x"),
        renderRunning(),
        renderStdout().element,
        renderTable(table()),
        renderDownload({ type: "download", value: "r", filename: "f" }),
        renderForm({ type: "form", href: "../n" }),
        renderImage({ type: "image", value: "i.png" }),
    ];

    let seen = 0;

    for (const element of elements) {
        for (const icon of find(element, ".ftw-icon")) {
            seen += 1;

            assert.equal(icon.tagName, "SPAN");
            assert.equal(icon.getAttribute("aria-hidden"), "true");
            assert.match(icon.className, /^ftw-icon ftw-icon-[a-z]+$/);
            assert.equal(icon.children.length, 0);
            assert.equal(icon.textContent, "");
        }
    }

    assert.ok(seen >= 8);
});

test("no renderer builds an svg at runtime", () => {
    const elements = [
        renderText({ type: "text", value: "x" }),
        renderError("x"),
        renderRunning(),
        renderStdout().element,
        renderTable(table()),
        renderDownload({ type: "download", value: "r", filename: "f" }),
        renderForm({ type: "form", href: "../n" }),
        renderImage({ type: "image", value: "i.png" }),
    ];

    assert.deepEqual(document.namespaced, []);

    for (const element of elements) {
        for (const tag of tagsIn(element)) {
            assert.ok(!SVG_TAGS.has(tag), `unexpected ${tag} element`);
        }
    }
});

test("every card is a div carrying the shared ftw-output class", () => {
    const cards = [
        renderText({ type: "text", value: "x" }),
        renderError("x"),
        renderRunning(),
        renderStdout().element,
        renderTable(table()),
        renderDownload({ type: "download", value: "r", filename: "f" }),
        renderForm({ type: "form", href: "../n" }),
        renderImage({ type: "image", value: "i.png" }),
    ];

    for (const card of cards) {
        assert.equal(card.tagName, "DIV");
        assert.ok(card.classes().has("ftw-output"));
        assert.equal([...card.classes()].length, 2);
    }
});

test("action buttons are typed buttons with a title", () => {
    const element = renderTable(table());

    for (const button of find(element, ".ftw-action")) {
        assert.equal(button.tagName, "BUTTON");
        assert.equal(button.type, "button");
        assert.notEqual(button.title, "");
    }
});
