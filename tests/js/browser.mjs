export function installClipboard() {
    const record = { texts: [], items: [] };

    Object.defineProperty(globalThis, "navigator", {
        value: {
            clipboard: {
                async writeText(text) {
                    record.texts.push(text);
                },
                async write(items) {
                    record.items.push(items);
                },
            },
        },
        writable: true,
        configurable: true,
    });

    globalThis.ClipboardItem = class ClipboardItem {
        constructor(payload) {
            this.payload = payload;
        }
    };

    return record;
}


export function installObjectUrls() {
    const record = { created: [], revoked: [] };

    URL.createObjectURL = (blob) => {
        const source = `blob:fake/${record.created.length}`;

        record.created.push({ source, blob });

        return source;
    };

    URL.revokeObjectURL = (source) => {
        record.revoked.push(source);
    };

    return record;
}


export function installTimers() {
    const pending = [];

    globalThis.setTimeout = (callback, delay) => {
        pending.push({ callback, delay });

        return pending.length;
    };

    return {
        pending,
        flush() {
            const queued = pending.splice(0, pending.length);

            for (const entry of queued) entry.callback();
        },
    };
}


export function installFetch(handler) {
    const calls = [];

    globalThis.fetch = async (url, options) => {
        calls.push({ url, options });

        return handler(url, options);
    };

    return calls;
}


export function streamOf(chunks) {
    const encoder = new TextEncoder();
    const queue = chunks.map(
        (chunk) => (typeof chunk === "string" ? encoder.encode(chunk) : chunk));

    let index = 0;

    return {
        getReader() {
            return {
                async read() {
                    if (index >= queue.length) {
                        return { done: true, value: undefined };
                    }

                    return { done: false, value: queue[index++] };
                },
            };
        },
    };
}


export function bytesOf(text) {
    return new TextEncoder().encode(text);
}


export function splitBytes(text, size) {
    const bytes = bytesOf(text);
    const chunks = [];

    for (let start = 0; start < bytes.length; start += size) {
        chunks.push(bytes.slice(start, start + size));
    }

    return chunks;
}


export function sse(name, data) {
    return `event: ${name}\ndata: ${JSON.stringify(data)}\n\n`;
}
