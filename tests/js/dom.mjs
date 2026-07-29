const FORBIDDEN_ATTRIBUTES =
    /^(?:on\w+|href|src|srcdoc|srcset|style|formaction|action|data|xlink:href)$/i;


class ClassList {
    constructor(owner) {
        this.owner = owner;
        this.names = new Set();
    }

    add(...names) {
        for (const name of names) {
            this.names.add(name);
        }
    }

    remove(...names) {
        for (const name of names) {
            this.names.delete(name);
        }
    }

    contains(name) {
        return this.names.has(name) || this.owner.classNames().has(name);
    }
}


class Listeners {
    constructor() {
        this.listeners = new Map();
    }

    addEventListener(type, callback) {
        if (!this.listeners.has(type)) {
            this.listeners.set(type, new Set());
        }

        this.listeners.get(type).add(callback);
    }

    removeEventListener(type, callback) {
        const registered = this.listeners.get(type);

        if (registered !== undefined) {
            registered.delete(callback);
        }
    }

    dispatch(type, event = {}) {
        const results = [];

        for (const callback of [...(this.listeners.get(type) ?? [])]) {
            results.push(callback({ type, ...event }));
        }

        return results;
    }

    dispatchEvent(event) {
        this.dispatch(event.type, event);
        return true;
    }
}


export class FakeElement extends Listeners {
    constructor(tagName) {
        super();

        this.tagName = tagName.toUpperCase();
        this.namespace = null;
        this.children = [];
        this.parent = null;
        this.attributes = {};
        this.classList = new ClassList(this);
        this.textContent = "";
        this.className = "";
        this.value = "";
        this.type = "";
        this.id = "";
        this.title = "";
        this.href = "";
        this.src = "";
        this.alt = null;
        this.download = null;
        this.hidden = false;
        this.disabled = false;
        this.checked = false;
        this.clicks = 0;
        this.scrolls = [];
    }

    classNames() {
        return new Set(String(this.className).split(/\s+/).filter(Boolean));
    }

    classes() {
        return new Set([...this.classNames(), ...this.classList.names]);
    }

    append(...nodes) {
        for (const node of nodes) {
            node.parent = this;
            this.children.push(node);
        }
    }

    replaceChildren(...nodes) {
        this.children = [];
        this.append(...nodes);
    }

    remove() {
        if (this.parent === null) {
            return;
        }

        const index = this.parent.children.indexOf(this);

        if (index !== -1) {
            this.parent.children.splice(index, 1);
        }

        this.parent = null;
    }

    set innerHTML(value) {
        throw new Error(
            `innerHTML is not allowed: output text must be inserted as text `
            + `(got ${JSON.stringify(String(value)).slice(0, 60)})`);
    }

    get innerHTML() {
        throw new Error("innerHTML is not allowed");
    }

    set outerHTML(value) {
        throw new Error("outerHTML is not allowed");
    }

    insertAdjacentHTML() {
        throw new Error("insertAdjacentHTML is not allowed");
    }

    setAttribute(name, value) {
        if (FORBIDDEN_ATTRIBUTES.test(name)) {
            throw new Error(`attribute is not allowed from output text: ${name}`);
        }

        this.attributes[name] = value;
    }

    getAttribute(name) {
        return name in this.attributes ? this.attributes[name] : null;
    }

    hasAttribute(name) {
        return name in this.attributes;
    }

    removeAttribute(name) {
        delete this.attributes[name];
    }

    matches(selector) {
        if (selector.startsWith(".")) return this.classes().has(selector.slice(1));
        if (selector.startsWith("#")) return this.id === selector.slice(1);

        return this.tagName === selector.toUpperCase();
    }

    querySelector(selector) {
        for (const node of walk(this)) {
            if (node !== this && node.matches(selector)) return node;
        }

        return null;
    }

    scrollIntoView(options) {
        this.scrolls.push(options);
    }

    click() {
        this.clicks += 1;
        return Promise.all(this.dispatch("click"));
    }
}


class FakeDocument extends Listeners {
    constructor() {
        super();

        this.body = new FakeElement("body");
        this.head = new FakeElement("head");
        this.created = [];
        this.namespaced = [];
        this.byId = new Map();
    }

    createElement(tagName) {
        const element = new FakeElement(tagName);

        this.created.push(element);

        return element;
    }

    createElementNS(namespace, tagName) {
        const element = new FakeElement(tagName);

        element.namespace = namespace;
        this.namespaced.push({ namespace, tagName });

        return element;
    }

    getElementById(id) {
        if (this.byId.has(id)) {
            return this.byId.get(id);
        }

        for (const root of [this.head, this.body]) {
            for (const node of walk(root)) {
                if (node.id === id) return node;
            }
        }

        return null;
    }

    querySelector(selector) {
        return this.body.querySelector(selector);
    }
}


export function walk(element) {
    const found = [element];

    for (const child of element.children) {
        found.push(...walk(child));
    }

    return found;
}


export function tagsIn(element) {
    return walk(element).map((node) => node.tagName);
}


export function find(element, selector) {
    return walk(element).filter((node) => node.matches(selector));
}


export function only(element, selector) {
    const found = find(element, selector);

    if (found.length !== 1) {
        throw new Error(
            `expected exactly one ${selector}, found ${found.length}`);
    }

    return found[0];
}


export function makeElement(tagName, attributes = {}) {
    const element = new FakeElement(tagName);

    Object.assign(element, attributes);

    return element;
}


export function installDocument() {
    const document = new FakeDocument();

    globalThis.HTMLElement = FakeElement;
    globalThis.document = document;

    return document;
}


export function installWindow() {
    const assigned = [];

    globalThis.window = {
        location: {
            assign(href) {
                assigned.push(href);
            },
        },
    };

    return assigned;
}
