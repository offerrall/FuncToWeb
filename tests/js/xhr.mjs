class FakeUpload {
    constructor() {
        this.listeners = new Map();
    }

    addEventListener(type, callback) {
        if (!this.listeners.has(type)) this.listeners.set(type, new Set());

        this.listeners.get(type).add(callback);
    }

    emit(type, event) {
        for (const callback of [...(this.listeners.get(type) ?? [])]) {
            callback(event);
        }
    }
}


export function installXhr() {
    const record = { scenarios: [], requests: [] };

    class FakeXhr {
        constructor() {
            this.method = null;
            this.url = null;
            this.headers = {};
            this.responseType = "";
            this.status = 0;
            this.response = null;
            this.body = null;
            this.upload = new FakeUpload();
            this.listeners = new Map();
        }

        open(method, url) {
            this.method = method;
            this.url = url;
        }

        setRequestHeader(name, value) {
            this.headers[name] = value;
        }

        addEventListener(type, callback) {
            if (!this.listeners.has(type)) this.listeners.set(type, new Set());

            this.listeners.get(type).add(callback);
        }

        emit(type, event) {
            for (const callback of [...(this.listeners.get(type) ?? [])]) {
                callback(event);
            }
        }

        send(body) {
            this.body = body;
            record.requests.push(this);

            const scenario = record.scenarios.shift() ?? { outcome: "load",
                                                           status: 200,
                                                           response: { uploaded: true } };

            queueMicrotask(() => {
                for (const loaded of scenario.progress ?? []) {
                    this.upload.emit("progress", { loaded });
                }

                if (scenario.outcome === "load") {
                    this.status = scenario.status ?? 200;
                    this.response = Object.hasOwn(scenario, "response")
                        ? scenario.response
                        : { uploaded: true };
                    this.emit("load", {});
                    return;
                }

                this.emit(scenario.outcome, {});
            });
        }
    }

    globalThis.XMLHttpRequest = FakeXhr;

    return record;
}


export function upload(log, name, size, reference = `ref-${name}`) {
    return {
        reference,
        file: { name, size },
        complete() {
            log.push(name);
        },
    };
}
