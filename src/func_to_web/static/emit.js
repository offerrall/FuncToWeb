const VERSION = 1;


function segment(pathname) {
    const parts = pathname.split("/").filter((part) => part !== "");

    return parts.length === 0 ? "" : parts[parts.length - 1];
}


function slug() {
    return segment(globalThis.window?.location?.pathname ?? "");
}


function host() {
    const window = globalThis.window;

    if (window === undefined || window === null) return null;

    const parent = window.parent;

    if (parent === undefined || parent === null || parent === window) return null;

    return parent;
}


export function emit(kind, payload = {}) {
    const parent = host();

    if (parent === null) return;

    parent.postMessage({ v: VERSION, kind, slug: slug(), ...payload }, "*");
}


export function observeHeight() {
    if (host() === null || typeof globalThis.ResizeObserver !== "function") return;

    const body = globalThis.document.body;
    let previous = 0;
    let scheduled = null;

    function measure() {
        scheduled = null;
        // The body's natural border box includes padding and can shrink.
        // documentElement.scrollHeight would retain the iframe's old height.
        const height = Math.ceil(body.getBoundingClientRect().height);
        if (height > 0 && height !== previous) {
            previous = height;
            emit("resize", { height });
        }
    }

    const observer = new ResizeObserver(() => {
        if (scheduled === null) scheduled = requestAnimationFrame(measure);
    });
    observer.observe(body, { box: "border-box" });
}
