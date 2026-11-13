import { emit, observeHeight } from "./emit.js";
import { compileForm } from "./form.js";
import {
    renderDownload, renderError, renderForm, renderImage, renderRunning,
    renderStdout, renderTable, renderText,
} from "./output.js";
import { callStream } from "./sdk.js";
import { runUploads } from "./upload.js";

const plan = JSON.parse(
    document.getElementById("functoweb-plan").textContent);
const hidden = JSON.parse(
    document.getElementById("functoweb-hidden").textContent);
const form = compileForm(plan, { hidden });

const labels = new Map(plan.fields.map((field) => [field.name, field.label]));

const autorun = JSON.parse(
    document.getElementById("functoweb-autorun").textContent);

const fields = document.getElementById("fields");
for (const field of form.fields) {
    fields.append(field.widget.el);
}

const result = document.getElementById("result");

function isStrings(value) {
    return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isTable(output) {
    return isStrings(output.headers)
        && Array.isArray(output.rows)
        && output.rows.every(isStrings);
}

function renderOutput(output) {
    if (output === null || typeof output !== "object") return null;

    if (output.type === "table") {
        return isTable(output) ? renderTable(output) : null;
    }

    if (typeof output.value !== "string") return null;

    if (output.type === "text") return renderText(output);
    if (output.type === "image") return renderImage(output);

    if (output.type === "download") {
        return typeof output.filename === "string" && output.filename !== ""
            ? renderDownload(output)
            : null;
    }

    return null;
}

function isForm(output) {
    return output !== null && typeof output === "object"
        && output.type === "form"
        && typeof output.href === "string" && output.href !== "";
}

function show(...elements) {
    result.replaceChildren(...elements);
    result.scrollIntoView({ behavior: "smooth", block: "start" });
}

function fail(message) {
    show(renderError(message));
}

function listed(candidates) {
    return candidates
        .map((field) => labels.get(field.name) ?? field.name)
        .join(", ");
}

function isRunError(envelope) {
    return envelope !== null && typeof envelope === "object"
        && Object.hasOwn(envelope, "error")
        && !Object.hasOwn(envelope, "result");
}

function showFailure(error, kept) {
    show(...kept, renderError(error.message));

    if (isRunError(error.envelope)) emit("error", { message: error.message });
}

function showResult(outputs, kept) {
    if (outputs.length === 1 && isForm(outputs[0])) {
        show(...kept, renderForm(outputs[0]));
        emit("navigate", { href: outputs[0].href });
        window.location.assign(outputs[0].href);
        return;
    }

    const elements = outputs.map(renderOutput);

    if (elements.includes(null)) {
        show(...kept, renderError("Invalid server response"));
        return;
    }

    show(...kept, ...elements);
    emit("result", { outputs });
}

async function run(body) {
    const running = renderRunning();
    const stdout = renderStdout();

    let printed = false;
    let outputs = null;
    let failure = null;

    try {
        outputs = await callStream(".", body, {
            onStart() {
                show(running);
            },
            onPrint(text) {
                if (!printed) {
                    printed = true;
                    show(stdout.element, running);
                }

                stdout.append(text);
            },
        });
    } catch (error) {
        failure = error;
    }

    const kept = printed ? [stdout.element] : [];

    if (failure === null) showResult(outputs, kept);
    else showFailure(failure, kept);

    if (printed) stdout.follow();
}

const submit = document.getElementById("submit");

submit.addEventListener("click", async () => {
    if (!form.isReady()) {
        form.showErrors();

        const broken = form.fields.filter((field) => field.widget.hasError());
        const missing = form.fields.filter(
            (field) => !field.widget.isReady() && !field.widget.hasError());

        const parts = [];
        if (broken.length) parts.push(`Fix: ${listed(broken)}`);
        if (missing.length) parts.push(`Complete: ${listed(missing)}`);

        fail(parts.join(" · "));
        return;
    }

    // busy brackets everything the click starts, uploads included, and its
    // false goes out whatever the outcome, so a host is never left waiting.
    emit("busy", { busy: true });

    try {
        const uploads = form.uploads();

        if (uploads.length > 0) {
            submit.disabled = true;

            const uploaded = await runUploads(uploads);

            submit.disabled = false;

            if (!uploaded) return;
        }

        submit.disabled = true;

        try {
            await run(form.read());
        } finally {
            submit.disabled = false;
        }
    } finally {
        emit("busy", { busy: false });
    }
});

emit("ready");
observeHeight();

if (autorun && form.isReady()) submit.click();
