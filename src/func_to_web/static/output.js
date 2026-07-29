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

function copyTextButton(value) {
    return actionButton("Copy to clipboard", copyIcon,
                        () => navigator.clipboard.writeText(value));
}

function copyImageButton(source) {
    return actionButton("Copy image", copyIcon, async () => {
        const blob = await (await fetch(source)).blob();

        await navigator.clipboard.write([
            new ClipboardItem({ [blob.type]: blob }),
        ]);
    });
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

export function renderStdout() {
    const { element, value } = block("stdout", "");

    element.append(mark(clockIcon()), value);

    return {
        element,
        append(text) {
            value.textContent += text;
        },
    };
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
