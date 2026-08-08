function icon(name) {
    const element = document.createElement("span");

    element.className = `ftw-icon ftw-icon-${name}`;
    element.setAttribute("aria-hidden", "true");

    return element;
}

const copyIcon = () => icon("copy");
const checkIcon = () => icon("check");
const alertIcon = () => icon("alert");
const downloadIcon = () => icon("download");
const clockIcon = () => icon("clock");

function mark(element) {
    element.classList.add("ftw-output-mark");
    return element;
}

function actions(...buttons) {
    const element = document.createElement("div");
    element.className = "ftw-actions";
    element.append(...buttons);
    return element;
}

function actionButton(title, drawing, action, confirms = true) {
    const button = document.createElement("button");

    button.type = "button";
    button.className = "ftw-action";
    button.title = title;
    button.append(drawing());

    button.addEventListener("click", async () => {
        try {
            await action();
        } catch {
            return;
        }

        if (!confirms) return;

        button.replaceChildren(checkIcon());
        button.classList.add("done");

        setTimeout(() => {
            button.replaceChildren(drawing());
            button.classList.remove("done");
        }, 2000);
    });

    return button;
}

// navigator.clipboard exists only in a secure context, and a page served
// over plain http from a LAN address is not one. That is where these apps
// are usually read, so the button has to work there
async function copyText(value) {
    if (typeof navigator.clipboard?.writeText === "function") {
        try {
            await navigator.clipboard.writeText(value);

            return;
        } catch {
            // outside a secure context the property is usually missing
            // altogether, but a browser may keep it and refuse the write.
            // Either way the fallback below is what is left
        }
    }

    const holder = document.createElement("textarea");

    holder.value = value;
    holder.setAttribute("readonly", "");
    holder.style.position = "fixed";
    holder.style.opacity = "0";

    document.body.append(holder);
    holder.select();

    try {
        if (!document.execCommand("copy")) {
            throw new Error("the browser refused to copy");
        }
    } finally {
        holder.remove();
    }
}

function copyTextButton(value) {
    return actionButton("Copy to clipboard", copyIcon,
                        () => copyText(value));
}

// a picture has no fallback: execCommand copies a selection, and there is
// no selection that carries an image. Rather than a button that ticks and
// leaves the clipboard empty, it says so and stays out of the way
function copyImageButton(source) {
    const able = globalThis.isSecureContext
        && typeof navigator.clipboard?.write === "function"
        && typeof globalThis.ClipboardItem === "function";

    const button = actionButton("Copy image", copyIcon, async () => {
        const blob = await (await fetch(source)).blob();

        await navigator.clipboard.write([
            new ClipboardItem({ [blob.type]: blob }),
        ]);
    });

    if (!able) {
        button.disabled = true;
        button.title = "Copying an image needs https or localhost. "
            + "Download it instead.";
    }

    return button;
}

function download(source, filename) {
    const link = document.createElement("a");

    link.href = source;
    link.download = filename;
    link.click();
}

function downloadButton(source, filename) {
    return actionButton("Download", downloadIcon, () => {
        download(source, filename);
    }, false);
}

function downloadTextButton(text, mediaType, filename) {
    return actionButton("Download", downloadIcon, () => {
        const source = URL.createObjectURL(new Blob([text], { type: mediaType }));

        download(source, filename);

        setTimeout(() => URL.revokeObjectURL(source), 10000);
    }, false);
}

function block(variant, text) {
    const element = document.createElement("div");
    element.className = `ftw-output ftw-output-${variant}`;

    const value = document.createElement("pre");
    value.className = "ftw-output-value";
    value.textContent = text;

    return { element, value };
}

export function renderText(output) {
    const { element, value } = block("text", output.value);

    element.append(
        mark(checkIcon()),
        value,
        actions(copyTextButton(output.value)),
    );

    return element;
}

export function renderError(message) {
    const { element, value } = block("error", message);

    element.append(mark(alertIcon()), value);

    return element;
}

export function renderRunning() {
    const { element, value } = block("running", "Running…");

    element.append(mark(clockIcon()), value);

    return element;
}

const STDOUT_CHARACTERS = 40000;

const STDOUT_TRIMMED = "… earlier output trimmed\n";

const STDOUT_SLACK = 4;

export function renderStdout() {
    const { element, value } = block("stdout", "");

    element.append(mark(clockIcon()), value);

    let text = "";
    let trimmed = false;
    let following = true;

    value.addEventListener("scroll", () => {
        following = atBottom(value);
    });

    function follow() {
        if (following) value.scrollTop = value.scrollHeight;
    }

    return {
        element,
        follow,
        append(chunk) {
            text += chunk;

            if (text.length > STDOUT_CHARACTERS) {
                text = fromWholeLine(text.slice(-STDOUT_CHARACTERS));
                trimmed = true;
            }

            value.textContent = trimmed ? STDOUT_TRIMMED + text : text;

            follow();
        },
    };
}

function fromWholeLine(text) {
    const start = text.indexOf("\n");

    return start === -1 ? text : text.slice(start + 1);
}

function atBottom(element) {
    const { scrollTop, scrollHeight, clientHeight } = element;

    if (typeof scrollHeight !== "number" || typeof clientHeight !== "number"
            || typeof scrollTop !== "number") {
        return true;
    }

    return scrollHeight - clientHeight - scrollTop <= STDOUT_SLACK;
}

function row(cells, tag) {
    const line = document.createElement("tr");

    for (const cell of cells) {
        const element = document.createElement(tag);
        element.textContent = cell;
        line.append(element);
    }

    return line;
}

function tabbed(output) {
    return [output.headers, ...output.rows]
        .map((cells) => cells.join("\t"))
        .join("\n");
}

const CSV_QUOTED = /[",\r\n]/;

function csvCell(value) {
    return CSV_QUOTED.test(value) ? `"${value.replaceAll('"', '""')}"` : value;
}

function csv(output) {
    return [output.headers, ...output.rows]
        .map((cells) => cells.map(csvCell).join(","))
        .join("\r\n");
}

export function renderTable(output) {
    const element = document.createElement("div");
    element.className = "ftw-output ftw-output-table";

    const grid = document.createElement("div");
    grid.className = "ftw-output-grid";

    const table = document.createElement("table");
    const head = document.createElement("thead");
    const body = document.createElement("tbody");

    head.append(row(output.headers, "th"));
    for (const cells of output.rows) body.append(row(cells, "td"));

    table.append(head, body);
    grid.append(table);

    element.append(
        mark(checkIcon()),
        grid,
        actions(
            copyTextButton(tabbed(output)),
            downloadTextButton(csv(output), "text/csv;charset=utf-8", "table.csv"),
        ),
    );

    return element;
}

export function renderDownload(output) {
    const element = document.createElement("div");
    element.className = "ftw-output ftw-output-download";

    const link = document.createElement("a");
    link.className = "ftw-download";
    link.href = `../returns/${encodeURIComponent(output.value)}`;
    link.download = output.filename;

    const name = document.createElement("span");
    name.textContent = output.filename;

    link.append(downloadIcon(), name);
    element.append(link);

    return element;
}

export function renderForm(output) {
    const element = document.createElement("div");
    element.className = "ftw-output ftw-output-form";

    const link = document.createElement("a");
    link.className = "ftw-download";
    link.href = output.href;

    const name = document.createElement("span");
    name.textContent = "Opening the form…";

    link.append(clockIcon(), name);
    element.append(link);

    return element;
}

export function renderImage(output) {
    const element = document.createElement("div");
    element.className = "ftw-output ftw-output-image";

    const image = document.createElement("img");
    image.className = "ftw-output-img";
    image.src = output.value;
    image.alt = "";

    element.append(
        image,
        actions(
            copyImageButton(output.value),
            downloadButton(output.value, "image.png"),
        ),
    );

    return element;
}
