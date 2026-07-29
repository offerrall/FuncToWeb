import { compileForm } from "./form.js";
import {
    renderDownload, renderError, renderForm, renderImage, renderRunning,
    renderStdout, renderTable, renderText,
} from "./output.js";
import { runUploads } from "./upload.js";

const plan = JSON.parse(
    document.getElementById("functoweb-plan").textContent);
const form = compileForm(plan);

const labels = new Map(plan.fields.map((field) => [field.name, field.label]));

const hidden = new Set(JSON.parse(
    document.getElementById("functoweb-hidden").textContent));

const fields = document.getElementById("fields");
for (const field of form.fields) {
    if (!hidden.has(field.name)) fields.append(field.widget.el);
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

function parseEvent(block) {
    const data = [];
    let name = null;

    for (const line of block.split("\n")) {
        if (line.startsWith("event:")) name = line.slice(6).trim();
        else if (line.startsWith("data:")) data.push(line.slice(5));
    }

    if (name === null) return null;

    try {
        return { name, data: JSON.parse(data.join("\n")) };
    } catch {
        return { name, data: null };
    }
}

async function* events(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";

    for (;;) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer = (buffer + decoder.decode(value, { stream: true }))
            .replace(/\r\n/g, "\n");

        let end = buffer.indexOf("\n\n");

        while (end !== -1) {
            const event = parseEvent(buffer.slice(0, end));

            buffer = buffer.slice(end + 2);

            if (event !== null) yield event;

            end = buffer.indexOf("\n\n");
        }
    }
}

function showResult(data, kept) {
    const hasResult = data !== null && typeof data === "object"
        && Object.hasOwn(data, "result");
    const hasError = data !== null && typeof data === "object"
        && Object.hasOwn(data, "error");

    if (hasResult === hasError) {
        show(...kept, renderError("Invalid server response"));
        return;
    }

    if (hasError) {
        show(...kept, renderError(data.error));
        return;
    }

    const outputs = Array.isArray(data.result) ? data.result : [data.result];

    if (outputs.length === 1 && isForm(outputs[0])) {
        show(...kept, renderForm(outputs[0]));
        window.location.assign(outputs[0].href);
        return;
    }

    const elements = outputs.map(renderOutput);

    if (elements.includes(null)) {
        show(...kept, renderError("Invalid server response"));
        return;
    }

    show(...kept, ...elements);
}

async function run(body) {
    let response;

    try {
        response = await fetch("invoke-stream", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            body: JSON.stringify(body),
        });
    } catch {
        fail("Invalid server response");
        return;
    }

    if (!response.ok || response.body === null) {
        fail("Invalid server response");
        return;
    }

    const running = renderRunning();
    const stdout = renderStdout();

    let printed = false;
    let answered = false;

    for await (const event of events(response)) {
        if (event.name === "start") {
            show(running);
            continue;
        }

        if (event.name === "print" && typeof event.data?.text === "string") {
            if (!printed) {
                printed = true;
                show(stdout.element, running);
            }

            stdout.append(event.data.text);
            continue;
        }

        if (event.name === "result") {
            answered = true;
            showResult(event.data, printed ? [stdout.element] : []);
        }
    }

    if (!answered) fail("Invalid server response");
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
});
