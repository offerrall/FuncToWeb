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
