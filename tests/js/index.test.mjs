import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

// The index has no module of its own: its script is inline in the template.
// It is read out of the template and run against the few browser objects it
// touches, so what is tested is the text that is served.
const TEMPLATE = readFileSync(
    new URL("../../src/func_to_web/templates/index.html", import.meta.url),
    "utf-8");

const SCRIPT = /<script type="module">([\s\S]*?)<\/script>/.exec(TEMPLATE)[1];

const ORIGIN = "http://host";


function makeLink(slug) {
    const link = {
        dataset: { slug },
        active: false,
        classList: {
            toggle: (name, on) => {
                assert.equal(name, "active");
                link.active = on;
            },
            contains: (name) => name === "active" && link.active,
        },
        scrollIntoView() {},
    };

    return link;
}


function open(slugs, { hash = "", prefix = "" } = {}) {
    const links = slugs.map(makeLink);
    const listeners = {};
    const loads = [];
    const frame = {
        location: {
            href: "about:blank",
            replace(src) {
                loads.push(src);
                this.href = ORIGIN + src;
            },
        },
    };
    const index = {
        links,
        loads,
        frame,
        navRemoved: false,
        location: { hash },
        replaced: [],
        active: () => links.filter((link) => link.active)
            .map((link) => link.dataset.slug),
        // What the browser does when a link of the sidebar is clicked: the
        // hash changes, and hashchange fires only if it really changed.
        click(slug) {
            if (index.location.hash === `#${slug}`) return;

            index.location.hash = `#${slug}`;
            listeners.hashchange();
        },
        // An OpenForm inside the iframe: the page moves itself and the new
        // page announces `ready`.
        opened(slug, query = "?prefill=%7B%7D") {
            frame.location.href = `${ORIGIN}${prefix}/${slug}/${query}`;
            index.post({ v: 1, kind: "ready", slug });
        },
        post(data, source = frame) {
            listeners.message({ source, data });
        },
    };
    const document = {
        getElementById: (id) => {
            assert.equal(id, "view");

            return { contentWindow: frame };
        },
        querySelectorAll: (selector) => {
            assert.equal(selector, "a[data-slug]");

            return links;
        },
        querySelector: (selector) => {
            assert.equal(selector, "nav");

            return { remove() { index.navRemoved = true; } };
        },
    };
    const history = {
        replaceState(state, unused, url) {
            index.replaced.push(url);
            index.location.hash = url;
        },
    };

    new Function("document", "addEventListener", "location", "history",
                 SCRIPT.replaceAll("__PREFIX__", prefix))(
        document,
        (type, callback) => { listeners[type] = callback; },
        index.location,
        history);

    return index;
}


test("the index opens on its first function when the hash names none", () => {
    const index = open(["alpha", "beta"]);

    assert.deepEqual(index.active(), ["alpha"]);
    assert.deepEqual(index.loads, ["/alpha/"]);
    assert.equal(index.navRemoved, false);
});


test("the index opens on the function its hash names", () => {
    const index = open(["alpha", "beta"], { hash: "#beta" });

    assert.deepEqual(index.active(), ["beta"]);
    assert.deepEqual(index.loads, ["/beta/"]);
});


test("an unknown hash falls back to the first function", () => {
    const index = open(["alpha", "beta"], { hash: "#gone" });

    assert.deepEqual(index.active(), ["alpha"]);
    assert.deepEqual(index.loads, ["/alpha/"]);
});


test("the prefix of the space leads every page the index loads", () => {
    const index = open(["alpha", "beta"], { prefix: "/tools" });

    index.click("beta");

    assert.deepEqual(index.loads, ["/tools/alpha/", "/tools/beta/"]);
});


test("clicking another function loads it and moves the highlight", () => {
    const index = open(["alpha", "beta"]);

    index.click("beta");

    assert.deepEqual(index.active(), ["beta"]);
    assert.deepEqual(index.loads, ["/alpha/", "/beta/"]);
});


test("clicking the function already on screen does not reload it", () => {
    // The hash goes from empty to #alpha, so hashchange does fire; reloading
    // would throw away whatever was typed in the form.
    const index = open(["alpha", "beta"]);

    index.click("alpha");

    assert.deepEqual(index.active(), ["alpha"]);
    assert.deepEqual(index.loads, ["/alpha/"]);
});


test("a space of one function has no sidebar", () => {
    const index = open(["alpha"]);

    assert.equal(index.navRemoved, true);
    assert.deepEqual(index.loads, ["/alpha/"]);
});


test("an OpenForm moves the highlight and the hash to the form it opened", () => {
    const index = open(["alpha", "beta"], { hash: "#alpha" });

    index.opened("beta");

    assert.deepEqual(index.active(), ["beta"]);
    assert.equal(index.location.hash, "#beta");
    assert.deepEqual(index.replaced, ["#beta"]);
});


test("following an OpenForm never reloads the prefilled page", () => {
    const index = open(["alpha", "beta"], { hash: "#alpha" });

    index.opened("beta");

    assert.deepEqual(index.loads, ["/alpha/"]);
    assert.equal(index.frame.location.href,
                 "http://host/beta/?prefill=%7B%7D");
});


test("the function that opened a form can be clicked again", () => {
    const index = open(["alpha", "beta"], { hash: "#alpha" });

    index.opened("beta");
    index.click("alpha");

    assert.deepEqual(index.active(), ["alpha"]);
    assert.deepEqual(index.loads, ["/alpha/", "/alpha/"]);
});


test("the page the index loaded itself leaves the hash alone", () => {
    const index = open(["alpha", "beta"]);

    index.post({ v: 1, kind: "ready", slug: "alpha" });

    assert.equal(index.location.hash, "");
    assert.deepEqual(index.replaced, []);
});


for (const [title, data] of [
    ["another kind", { v: 1, kind: "navigate", slug: "beta", href: "../beta/" }],
    ["a result", { v: 1, kind: "result", slug: "beta", outputs: [] }],
    ["another protocol version", { v: 2, kind: "ready", slug: "beta" }],
    ["a slug outside the space", { v: 1, kind: "ready", slug: "gamma" }],
    ["no slug", { v: 1, kind: "ready" }],
    ["null", null],
    ["a string", "ready"],
]) {
    test(`the sidebar ignores a message that is ${title}`, () => {
        const index = open(["alpha", "beta"], { hash: "#alpha" });

        index.post(data);

        assert.deepEqual(index.active(), ["alpha"]);
        assert.equal(index.location.hash, "#alpha");
        assert.deepEqual(index.loads, ["/alpha/"]);
    });
}


test("the sidebar ignores a ready that is not from its own iframe", () => {
    const index = open(["alpha", "beta"], { hash: "#alpha" });

    index.post({ v: 1, kind: "ready", slug: "beta" }, {});

    assert.deepEqual(index.active(), ["alpha"]);
    assert.equal(index.location.hash, "#alpha");
});
