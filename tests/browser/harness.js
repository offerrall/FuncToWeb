// Shared helpers for the real-browser verification pages of tests/browser.
//
// Every page here is opened by headless Chrome through the `verify` fixture of
// tests/browser/conftest.py, which serves the page from the very application
// under test, so the page and the application share an origin and an iframe of
// a served page can be read and driven from the harness.
//
//   chrome --headless=new --disable-gpu --no-sandbox \
//     --virtual-time-budget=20000 --dump-dom \
//     "http://127.0.0.1:PORT/harness/PAGE.html?base=...&hold=...&case=..."
//
// The verdict is read back from the #result element of the dumped DOM: "PASS"
// or "FAIL (n)". The named checks are written to #log so a failure says which
// one broke.
//
// Waiting: --virtual-time-budget is *virtual* time. Timers fire instantly, so
// a setTimeout is not a wait at all, and the DOM is dumped as soon as the
// budget runs out. Virtual time does pause while a network fetch is pending,
// which is what `hold()` exploits: every poll round parks the page on a real
// request to /harness-hold, so the loop waits in real time while spending
// almost none of the budget. Nothing here sleeps for a fixed duration; every
// wait ends on an observable condition.

const params = new URLSearchParams(location.search);

export const BASE = params.get("base");
export const HOLD = params.get("hold");
export const CASE = params.get("case");

const log = [];
let failures = 0;

export function check(name, condition, detail = "") {
    const ok = condition === true;

    if (!ok) {
        failures += 1;
    }

    log.push(`${ok ? "ok  " : "FAIL"}  ${name}`
             + (ok || detail === "" ? "" : `   ${detail}`));

    return ok;
}

export function equal(name, got, want) {
    return check(
        name,
        JSON.stringify(got) === JSON.stringify(want),
        `got ${JSON.stringify(got)}, want ${JSON.stringify(want)}`,
    );
}

export function note(text) {
    log.push(`--  ${text}`);
}

export async function hold(ms = 40) {
    await fetch(`${HOLD}?ms=${ms}`, { cache: "no-store" });
}

export async function waitFor(name, predicate, rounds = 250) {
    for (let round = 0; round < rounds; round += 1) {
        let value = null;

        try {
            value = predicate();
        } catch {
            value = null;
        }

        if (value) {
            return value;
        }

        await hold(40);
    }

    check(`waiting for ${name}`, false, "timed out");

    return null;
}

export async function openPage(path) {
    const frame = document.createElement("iframe");

    frame.width = "1024";
    frame.height = "768";
    document.getElementById("stage").append(frame);

    await new Promise((resolve) => {
        frame.addEventListener("load", resolve, { once: true });
        frame.src = `${BASE}${path}`;
    });

    const page = {
        frame,
        doc: frame.contentDocument,
        win: frame.contentWindow,
    };

    await waitFor("the widgets to mount",
                  () => page.doc.querySelector(".pth-field") !== null);

    return page;
}

export function labelOf(field) {
    const label = field.querySelector(
        ":scope > .pth-field-header > .pth-label");

    return label === null ? null : label.textContent;
}

export function fieldOf(root, name) {
    return [...root.querySelectorAll(".pth-field")]
        .find((field) => labelOf(field) === name) ?? null;
}

export function controlOf(
    root, name, selector = "input:not(.pth-toggle), textarea, select",
) {
    const field = fieldOf(root, name);

    return field === null ? null : field.querySelector(selector);
}

export function windowOf(node) {
    return node.ownerDocument.defaultView;
}

export function setValue(control, value) {
    const win = windowOf(control);

    if (control.type === "checkbox") {
        control.checked = value === true;
    } else {
        control.value = String(value);
    }

    control.dispatchEvent(new win.Event("input", { bubbles: true }));
    control.dispatchEvent(new win.Event("change", { bubbles: true }));
}

export function chooseOption(select, label) {
    const option = [...select.options]
        .find((candidate) => candidate.textContent === label);

    if (option === undefined) {
        check(`the select offers ${label}`, false,
              [...select.options].map((each) => each.textContent).join("|"));
        return;
    }

    select.value = option.value;
    select.dispatchEvent(new Event("change", { bubbles: true }));
}

export function typeInto(root, name, value) {
    const control = controlOf(root, name);

    if (control === null) {
        check(`a control named ${name} exists`, false);
        return null;
    }

    setValue(control, value);

    return control;
}

export function textFile(win, name, text) {
    return new win.File([text], name, { type: "text/plain" });
}

export function sizedFile(win, name, bytes) {
    return new win.File(["x".repeat(bytes)], name, { type: "text/plain" });
}

export function pick(input, files) {
    const win = windowOf(input);
    const transfer = new win.DataTransfer();

    for (const file of files) {
        transfer.items.add(file);
    }

    input.files = transfer.files;
    input.dispatchEvent(new win.Event("change", { bubbles: true }));
}

export function fileInputOf(root, name) {
    const field = fieldOf(root, name);

    return field === null ? null : field.querySelector(".pth-file-input");
}

export function resources(win) {
    return [
        ...win.performance.getEntriesByType("navigation"),
        ...win.performance.getEntriesByType("resource"),
    ];
}

export function failedResources(win) {
    return resources(win)
        .filter((entry) => typeof entry.responseStatus === "number"
                        && (entry.responseStatus === 0
                            || entry.responseStatus >= 400))
        .map((entry) => [entry.name, entry.responseStatus]);
}

export function requested(win, fragment) {
    return resources(win).filter((entry) => entry.name.includes(fragment));
}

// A PerformanceResourceTiming entry is recorded when the response finishes,
// which for a streamed run is a beat after the DOM already shows the answer,
// and for a mask-image a beat after the glyph is painted. Counting them right
// after the observable change is a race; waiting for them is not.
export async function awaitRequests(win, fragment, howMany,
                                    keep = () => true) {
    const found = await waitFor(
        `${howMany} request(s) for ${fragment}`,
        () => {
            const entries = requested(win, fragment).filter(keep);

            return entries.length >= howMany ? entries : null;
        });

    return found ?? [];
}

export function outputs(doc) {
    return [...doc.getElementById("result").querySelectorAll(":scope > *")];
}

export function outputKinds(doc) {
    return outputs(doc).map((element) => element.className);
}

export function resultText(doc) {
    return doc.getElementById("result").textContent;
}

export async function submit(page) {
    page.doc.getElementById("submit").click();
}

export async function runToResult(page) {
    await submit(page);

    const output = await waitFor(
        "an output to be rendered",
        () => page.doc.querySelector(
            "#result .ftw-output-text, #result .ftw-output-error, "
            + "#result .ftw-output-table, #result .ftw-output-image, "
            + "#result .ftw-output-download, #result .ftw-output-form"),
    );

    // The output is rendered from inside the event loop; page.js only frees
    // the submit in the finally that follows, so returning here would let a
    // caller click a button that is still disabled and lose the run.
    await waitFor("the submit to be freed",
                  () => page.doc.getElementById("submit").disabled === false);

    return output;
}

export async function compiledForm(path) {
    const { compileForm } = await import(`${BASE}static/form.js`);

    const html = await (await fetch(`${BASE}${path}`)).text();
    const parsed = new DOMParser().parseFromString(html, "text/html");
    const plan = JSON.parse(
        parsed.getElementById("functoweb-plan").textContent);

    const form = compileForm(plan);
    const host = document.createElement("div");

    host.className = "pth-root";
    document.getElementById("stage").append(host);

    for (const field of form.fields) {
        host.append(field.widget.el);
    }

    return { form, host, plan };
}

export function fieldNamed(form, name) {
    return form.fields.find((field) => field.name === name) ?? null;
}

export function report() {
    document.getElementById("log").textContent = log.join("\n");
    document.getElementById("result").textContent =
        failures === 0 ? "PASS" : `FAIL (${failures})`;
}

export async function run(cases) {
    try {
        const chosen = cases[CASE];

        if (chosen === undefined) {
            check(`the page knows the case ${CASE}`, false);
        } else {
            await chosen();
        }
    } catch (error) {
        check("the page ran without throwing", false,
              String(error && error.stack ? error.stack : error));
    }

    report();
}
