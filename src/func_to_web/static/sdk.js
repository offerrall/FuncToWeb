export class FuncToWebError extends Error {
    constructor(message, { status = null, url = null, envelope = null } = {}) {
        super(message);

        this.name = "FuncToWebError";
        this.status = status;
        this.url = url;
        this.envelope = envelope;
    }
}


const FILE_SLUG_LIMIT = 15;

const MODAL_STYLE_ID = "functoweb-modal-style";

const ASCII_FOLDINGS = {
    "ß": "ss", "æ": "ae", "œ": "oe", "ø": "o", "å": "a", "đ": "d", "ð": "d",
    "þ": "th", "ł": "l", "ı": "i",
};

const MODAL_STYLE = `
.ftw-frame {
    width: 100%;
    height: 100%;
    border: 0;
}

.ftw-modal {
    position: fixed;
    inset: 0;
    z-index: 2147483647;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    background: rgba(0, 0, 0, 0.55);
}

.ftw-modal-panel {
    position: relative;
    display: block;
    width: min(760px, 100%);
    height: min(760px, 100%);
    overflow: hidden;
    border-radius: 12px;
    background: transparent;
}

.ftw-modal-close {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 30px;
    height: 30px;
    padding: 0;
    border: 0;
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.55);
    color: #ffffff;
    font: inherit;
    line-height: 1;
    cursor: pointer;
}
`;


function asciiSlug(text) {
    return text
        .normalize("NFD")
        .replace(/\p{M}+/gu, "")
        .toLowerCase()
        .replace(/[ßæœøåđðþłı]/gu, (char) => ASCII_FOLDINGS[char])
        .replace(/[^a-z0-9]+/gu, "-")
        .replace(/^-+|-+$/gu, "")
        .slice(0, FILE_SLUG_LIMIT)
        .replace(/-+$/u, "");
}


function hexadecimal(bytes) {
    return [...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}


function uuid() {
    const source = globalThis.crypto;

    if (source === undefined || source === null) {
        throw new FuncToWebError(
            "crypto is unavailable: pass a reference of your own");
    }

    if (typeof source.randomUUID === "function") {
        return source.randomUUID();
    }

    const bytes = source.getRandomValues(new Uint8Array(16));

    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;

    const text = hexadecimal(bytes);

    return [
        text.slice(0, 8), text.slice(8, 12), text.slice(12, 16),
        text.slice(16, 20), text.slice(20),
    ].join("-");
}


export function fileReference(filename) {
    const dot = filename.lastIndexOf(".");
    const extension = dot > 0 ? filename.slice(dot) : "";
    const slug = asciiSlug(filename.slice(0, filename.length - extension.length));

    return slug === "" ? `${uuid()}${extension}` : `${slug}-${uuid()}${extension}`;
}


function trimmed(url) {
    if (typeof url !== "string") {
        throw new FuncToWebError("the url must be a string");
    }

    return url.replace(/\/+$/u, "");
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


async function* sent(response) {
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


function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}


async function decoded(response) {
    try {
        return await response.json();
    } catch {
        return null;
    }
}


function refusal(response, payload) {
    if (isRecord(payload) && typeof payload.detail === "string") {
        return payload.detail;
    }

    if (isRecord(payload) && payload.detail !== undefined) {
        return JSON.stringify(payload.detail);
    }

    return `the answer of ${response.url || "the server"} is not an envelope `
        + `(HTTP ${response.status})`;
}


async function envelopeOf(response, url) {
    const payload = await decoded(response);

    if (isRecord(payload)
        && (Object.hasOwn(payload, "result") || Object.hasOwn(payload, "error"))) {
        return payload;
    }

    if (response.ok && isRecord(payload)) {
        return payload;
    }

    throw new FuncToWebError(refusal(response, payload), {
        status: response.status,
        url,
        envelope: payload,
    });
}


export function outputsOf(envelope, { url = null, status = null } = {}) {
    if (!isRecord(envelope)) {
        throw new FuncToWebError("the answer is not a JSON object",
                                 { url, status, envelope });
    }

    const answered = Object.hasOwn(envelope, "result");
    const failed = Object.hasOwn(envelope, "error");

    if (answered === failed) {
        throw new FuncToWebError(
            "the answer carries neither result nor error, or carries both",
            { url, status, envelope });
    }

    if (failed) {
        throw new FuncToWebError(String(envelope.error),
                                 { url, status, envelope });
    }

    return Array.isArray(envelope.result) ? envelope.result : [envelope.result];
}


function posted(url, args, signal) {
    if (!isRecord(args)) {
        throw new FuncToWebError("the arguments must be a plain object", { url });
    }

    return {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(args),
        signal,
    };
}


export async function call(url, args = {}, { signal = null } = {}) {
    const target = `${trimmed(url)}/invoke`;
    const response = await globalThis.fetch(target, posted(target, args, signal));

    return outputsOf(await envelopeOf(response, target),
                     { url: target, status: response.status });
}


export async function* events(url, args = {}, { signal = null } = {}) {
    const target = `${trimmed(url)}/invoke-stream`;
    const options = posted(target, args, signal);

    options.headers.Accept = "text/event-stream";

    const response = await globalThis.fetch(target, options);

    if (!response.ok || response.body === null || response.body === undefined) {
        throw new FuncToWebError(refusal(response, await decoded(response)),
                                 { url: target, status: response.status });
    }

    yield* sent(response);
}


export async function callStream(url, args = {}, options = {}) {
    const { onStart = null, onPrint = null, signal = null } = options;
    const target = `${trimmed(url)}/invoke-stream`;

    let envelope = null;

    for await (const event of events(url, args, { signal })) {
        if (event.name === "start") {
            if (onStart !== null) onStart();
        } else if (event.name === "print") {
            if (onPrint !== null && typeof event.data?.text === "string") {
                onPrint(event.data.text);
            }
        } else if (event.name === "result") {
            envelope = event.data;
        }
    }

    if (envelope === null) {
        throw new FuncToWebError("the stream ended with no result event",
                                 { url: target });
    }

    return outputsOf(envelope, { url: target, status: 200 });
}


export async function upload(spaceUrl, file, options = {}) {
    const { reference = null, signal = null } = options;
    const target = `${trimmed(spaceUrl)}/upload`;
    const chosen = reference ?? fileReference(file.name ?? "file");

    const response = await globalThis.fetch(target, {
        method: "POST",
        headers: {
            "Content-Type": "application/octet-stream",
            "X-File-Reference": chosen,
        },
        body: file,
        signal,
    });

    const payload = await decoded(response);

    if (!response.ok || !isRecord(payload) || payload.uploaded !== true) {
        throw new FuncToWebError(refusal(response, payload),
                                 { url: target, status: response.status });
    }

    return chosen;
}


export async function doc(spaceUrl, { signal = null } = {}) {
    const target = `${trimmed(spaceUrl)}/doc`;

    const response = await globalThis.fetch(target, {
        headers: { Accept: "text/plain" },
        signal,
    });

    if (!response.ok) {
        throw new FuncToWebError(refusal(response, await decoded(response)),
                                 { url: target, status: response.status });
    }

    return await response.text();
}


export function downloadUrl(spaceUrl, reference) {
    return `${trimmed(spaceUrl)}/returns/${encodeURIComponent(reference)}`;
}


export function formUrl(spaceUrl, output) {
    const href = output.href;

    return href.startsWith("../")
        ? `${trimmed(spaceUrl)}/${href.slice(3)}`
        : href;
}


export function pageUrl(url, { prefill = null, hidden = null } = {}) {
    const page = `${trimmed(url)}/`;
    const query = new URLSearchParams();

    if (prefill !== null) query.set("prefill", JSON.stringify(prefill));
    if (hidden !== null) query.set("hidden", JSON.stringify(hidden));

    const search = query.toString();

    return search === "" ? page : `${page}?${search}`;
}


function element(target) {
    const found = typeof target === "string"
        ? globalThis.document.querySelector(target)
        : target;

    if (found === null || found === undefined) {
        throw new FuncToWebError(`no element matches ${String(target)}`);
    }

    return found;
}


function styled() {
    const document = globalThis.document;

    if (document.getElementById(MODAL_STYLE_ID) !== null) return;

    const style = document.createElement("style");

    style.id = MODAL_STYLE_ID;
    style.textContent = MODAL_STYLE;

    document.head.append(style);
}


export function embed(target, url, options = {}) {
    const parent = element(target);
    const frame = globalThis.document.createElement("iframe");

    styled();

    frame.className = "ftw-frame";
    frame.src = pageUrl(url, options);
    frame.title = options.title ?? "";

    parent.append(frame);

    return frame;
}


export function openModal(url, options = {}) {
    const { onClose = null, ...rest } = options;
    const document = globalThis.document;

    styled();

    const overlay = document.createElement("div");
    const panel = document.createElement("div");
    const button = document.createElement("button");

    overlay.className = "ftw-modal";
    panel.className = "ftw-modal-panel";
    button.className = "ftw-modal-close";
    button.type = "button";
    button.textContent = "×";
    button.setAttribute("aria-label", "Close");

    panel.append(button);
    overlay.append(panel);

    const frame = embed(panel, url, rest);

    let open = true;

    function escaped(event) {
        if (event.key === "Escape") close();
    }

    function close() {
        if (!open) return;

        open = false;

        document.removeEventListener("keydown", escaped);
        overlay.remove();

        if (onClose !== null) onClose();
    }

    button.addEventListener("click", close);

    overlay.addEventListener("click", (event) => {
        if (event.target === overlay) close();
    });

    document.addEventListener("keydown", escaped);
    document.body.append(overlay);

    return { element: overlay, iframe: frame, close };
}
