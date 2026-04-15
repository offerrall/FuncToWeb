(function() {
    const COPY_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`;
    const CHECK_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`;
    const EXPAND_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>`;
    const CLOSE_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
    const DOWNLOAD_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`;

    function makeCopyButton(textToCopy) {
        const btn = document.createElement("button");
        btn.className = "functoweb-copy-btn";
        btn.innerHTML = COPY_SVG;
        btn.title = "Copy to clipboard";
        btn.addEventListener("click", () => {
            navigator.clipboard.writeText(textToCopy).then(() => {
                btn.innerHTML = CHECK_SVG;
                btn.classList.add("copied");
                setTimeout(() => {
                    btn.innerHTML = COPY_SVG;
                    btn.classList.remove("copied");
                }, 2000);
            });
        });
        return btn;
    }

    function makeBlock(variant) {
        const block = document.createElement("div");
        block.className = `functoweb-result-block functoweb-result-${variant}`;
        return block;
    }

    function makeLabel(text) {
        const label = document.createElement("div");
        label.className = "functoweb-result-label";
        label.textContent = text;
        return label;
    }

    function makeDownloadButton(csv, filename) {
        const btn = document.createElement("button");
        btn.className = "functoweb-copy-btn";
        btn.innerHTML = DOWNLOAD_SVG;
        btn.title = "Download as CSV";
        btn.addEventListener("click", () => {
            const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        });
        return btn;
    }

    function tableToCsv(headers, rows) {
        const escape = (v) => `"${String(v).replace(/"/g, '""')}"`;
        const lines = [headers.map(escape).join(",")];
        for (const row of rows) {
            lines.push(row.map(escape).join(","));
        }
        return lines.join("\n");
    }

    function buildTable(headers, rows) {
        const table = document.createElement("table");
        table.className = "functoweb-table";

        const thead = document.createElement("thead");
        const headRow = document.createElement("tr");
        for (const h of headers) {
            const th = document.createElement("th");
            th.textContent = h;
            headRow.appendChild(th);
        }
        thead.appendChild(headRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");
        for (const row of rows) {
            const tr = document.createElement("tr");
            for (const cell of row) {
                const td = document.createElement("td");
                td.textContent = cell;
                tr.appendChild(td);
            }
            tbody.appendChild(tr);
        }
        table.appendChild(tbody);

        return table;
    }

    function buildActionTable(headers, rows, action) {
        const table = document.createElement("table");
        table.className = "functoweb-table functoweb-table-action";

        const thead = document.createElement("thead");
        const headRow = document.createElement("tr");
        for (const h of headers) {
            const th = document.createElement("th");
            th.textContent = h;
            headRow.appendChild(th);
        }
        thead.appendChild(headRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");
        rows.forEach((row, i) => {
            const tr = document.createElement("tr");
            tr.style.cursor = "pointer";
            tr.dataset.rowIndex = i;
            for (const cell of row) {
                const td = document.createElement("td");
                td.textContent = cell;
                tr.appendChild(td);
            }
            tbody.appendChild(tr);
        });

        tbody.addEventListener("click", (e) => {
            const tr = e.target.closest("tr[data-row-index]");
            if (!tr) return;
            const row = rows[parseInt(tr.dataset.rowIndex, 10)];
            const params = new URLSearchParams();
            headers.forEach((h, i) => params.set(h, row[i]));
            window.location.href = `${action}?${params}`;
        });

        table.appendChild(tbody);

        return table;
    }

    const SDT_JS = "https://cdnjs.cloudflare.com/ajax/libs/simple-datatables/10.0.0/simple-datatables.min.js";
    const SDT_CSS = "https://cdnjs.cloudflare.com/ajax/libs/simple-datatables/10.0.0/style.min.css";

    const SDT_OVERRIDES = `
.datatable-wrapper { font-family: var(--functoweb-font-family) !important; color: var(--functoweb-surface-text) !important; }
.datatable-top, .datatable-bottom { padding: 0.5rem 0.75rem !important; background: transparent !important; }
.datatable-top { border-bottom: 1px solid var(--functoweb-surface-border) !important; }
.datatable-bottom { border-top: 1px solid var(--functoweb-surface-border) !important; }
.datatable-input { background: var(--functoweb-surface-bg) !important; border: 1px solid var(--functoweb-surface-border) !important; border-radius: var(--functoweb-nav-link-border-radius) !important; color: var(--functoweb-surface-text) !important; font-family: var(--functoweb-font-family) !important; font-size: 0.8125rem !important; padding: 0.375rem 0.625rem !important; }
.datatable-input:focus { outline: 2px solid var(--functoweb-surface-focus) !important; outline-offset: -1px !important; }
.datatable-selector { background: var(--functoweb-surface-bg) !important; border: 1px solid var(--functoweb-surface-border) !important; border-radius: var(--functoweb-nav-link-border-radius) !important; color: var(--functoweb-surface-text) !important; font-family: var(--functoweb-font-family) !important; font-size: 0.8125rem !important; padding: 0.25rem 0.5rem !important; }
.datatable-info { color: var(--functoweb-description-color) !important; font-size: 0.75rem !important; font-family: var(--functoweb-font-family) !important; }
.datatable-pagination a, .datatable-pagination button { display: inline-flex !important; align-items: center !important; justify-content: center !important; min-width: 2rem !important; height: 2rem !important; padding: 0 0.5rem !important; border: 1px solid var(--functoweb-surface-border) !important; border-radius: var(--functoweb-nav-link-border-radius) !important; background: var(--functoweb-surface-bg) !important; color: var(--functoweb-surface-text) !important; font-size: 0.8125rem !important; font-family: var(--functoweb-font-family) !important; text-decoration: none !important; cursor: pointer !important; transition: all 0.15s ease !important; }
.datatable-pagination a:hover, .datatable-pagination button:hover { background: var(--functoweb-nav-link-hover-bg) !important; border-color: var(--functoweb-surface-focus) !important; }
.datatable-pagination .datatable-active a, .datatable-pagination .datatable-active button { background: var(--functoweb-button-bg) !important; border-color: var(--functoweb-button-bg) !important; color: #fff !important; }
.datatable-pagination .datatable-disabled a, .datatable-pagination .datatable-disabled button { opacity: 0.4 !important; cursor: not-allowed !important; }
.datatable-sorter { color: inherit !important; }
.datatable-sorter::before { border-top-color: var(--functoweb-description-color) !important; }
.datatable-sorter::after { border-bottom-color: var(--functoweb-description-color) !important; }
.datatable-empty { color: var(--functoweb-description-color) !important; font-family: var(--functoweb-font-family) !important; }
.datatable-table th button, .datatable-pagination-list button { font-family: var(--functoweb-font-family) !important; }
`;

    let _sdtLoaded = null;

    function loadSimpleDatatables() {
        if (_sdtLoaded === true) return Promise.resolve(true);
        if (_sdtLoaded === false) return Promise.resolve(false);

        return new Promise((resolve) => {
            const link = document.createElement("link");
            link.rel = "stylesheet";
            link.href = SDT_CSS;
            document.head.insertBefore(link, document.head.firstChild);

            const style = document.createElement("style");
            style.textContent = SDT_OVERRIDES;
            document.head.appendChild(style);

            const script = document.createElement("script");
            script.src = SDT_JS;
            script.onload = () => { _sdtLoaded = true; resolve(true); };
            script.onerror = () => { _sdtLoaded = false; resolve(false); };
            document.head.appendChild(script);
        });
    }

    function enhanceTable(tableEl) {
        loadSimpleDatatables().then((ok) => {
            if (!ok || !window.simpleDatatables) return;
            new window.simpleDatatables.DataTable(tableEl, {
                searchable: true,
                sortable: true,
                fixedHeight: true,
                perPage: 10,
                perPageSelect: [5, 10, 25, 50],
                labels: {
                    placeholder: "Search...",
                    perPage: "rows per page",
                    noRows: "No entries found",
                    info: "Showing {start} to {end} of {rows} entries",
                },
            });
        });
    }

    function openTableOverlay(headers, rows) {
        const overlay = document.createElement("div");
        overlay.className = "functoweb-table-overlay";

        const inner = document.createElement("div");
        inner.className = "functoweb-table-overlay-inner";

        const header = document.createElement("div");
        header.className = "functoweb-table-overlay-header";

        const title = document.createElement("span");
        title.className = "functoweb-table-overlay-title";
        title.textContent = `${rows.length} row${rows.length !== 1 ? "s" : ""} \u00d7 ${headers.length} column${headers.length !== 1 ? "s" : ""}`;
        header.appendChild(title);

        const actions = document.createElement("div");
        actions.style.cssText = "display:flex;align-items:center;gap:0.375rem;";
        const csv = tableToCsv(headers, rows);
        actions.appendChild(makeDownloadButton(csv, "table.csv"));
        actions.appendChild(makeCopyButton(csv));

        const closeBtn = document.createElement("button");
        closeBtn.className = "functoweb-table-overlay-close";
        closeBtn.innerHTML = CLOSE_SVG;
        closeBtn.title = "Close";
        closeBtn.addEventListener("click", () => overlay.remove());
        actions.appendChild(closeBtn);

        header.appendChild(actions);
        inner.appendChild(header);

        const body = document.createElement("div");
        body.className = "functoweb-table-overlay-body";
        const table = buildTable(headers, rows);
        body.appendChild(table);
        inner.appendChild(body);

        overlay.appendChild(inner);
        document.body.appendChild(overlay);

        enhanceTable(table);

        requestAnimationFrame(() => {
            overlay.addEventListener("click", (e) => {
                if (e.target === overlay) overlay.remove();
            });
        });
    }

    const renderers = {
        text(payload) {
            const text = typeof payload === "object" ? (payload.data ?? String(payload)) : String(payload);
            const body = document.createElement("div");
            body.className = "functoweb-result-body";

            const pre = document.createElement("pre");
            pre.className = "functoweb-result-text";
            pre.textContent = text;
            body.appendChild(pre);
            body.appendChild(makeCopyButton(text));

            return body;
        },

        image(payload) {
            const src = typeof payload === "object" ? payload.data : payload;
            const body = document.createElement("div");
            body.className = "functoweb-result-body functoweb-result-image";

            const img = document.createElement("img");
            img.className = "functoweb-result-img";
            img.src = src;
            body.appendChild(img);

            const expandBtn = document.createElement("button");
            expandBtn.className = "functoweb-expand-btn";
            expandBtn.innerHTML = EXPAND_SVG;
            expandBtn.title = "View full size";
            expandBtn.addEventListener("click", () => {
                const overlay = document.createElement("div");
                overlay.className = "functoweb-image-overlay";

                const fullImg = document.createElement("img");
                fullImg.className = "functoweb-image-overlay-img";
                fullImg.src = src;
                overlay.appendChild(fullImg);

                overlay.addEventListener("click", () => overlay.remove());
                document.body.appendChild(overlay);
            });
            body.appendChild(expandBtn);

            return body;
        },

        table(payload) {
            const headers = payload.headers || [];
            const rows = payload.rows || [];

            const body = document.createElement("div");
            body.className = "functoweb-result-body functoweb-result-table";

            const wrapper = document.createElement("div");
            wrapper.className = "functoweb-table-wrapper";
            const table = buildTable(headers, rows);
            wrapper.appendChild(table);
            body.appendChild(wrapper);

            const actions = document.createElement("div");
            actions.className = "functoweb-table-actions";

            const count = document.createElement("span");
            count.className = "functoweb-table-row-count";
            count.textContent = `${rows.length} row${rows.length !== 1 ? "s" : ""}`;
            actions.appendChild(count);

            const expandBtn = document.createElement("button");
            expandBtn.className = "functoweb-copy-btn";
            expandBtn.innerHTML = EXPAND_SVG;
            expandBtn.title = "View full size";
            expandBtn.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                openTableOverlay(headers, rows);
            });
            actions.appendChild(expandBtn);

            const csv = tableToCsv(headers, rows);
            actions.appendChild(makeDownloadButton(csv, "table.csv"));
            actions.appendChild(makeCopyButton(csv));

            body.appendChild(actions);

            enhanceTable(table);

            return body;
        },

        action_table(payload) {
            const headers = payload.headers || [];
            const rows = payload.rows || [];
            const action = payload.action;

            const body = document.createElement("div");
            body.className = "functoweb-result-body functoweb-result-table";

            const wrapper = document.createElement("div");
            wrapper.className = "functoweb-table-wrapper";
            const table = buildActionTable(headers, rows, action);
            wrapper.appendChild(table);
            body.appendChild(wrapper);

            const actions = document.createElement("div");
            actions.className = "functoweb-table-actions";

            const count = document.createElement("span");
            count.className = "functoweb-table-row-count";
            count.textContent = `${rows.length} row${rows.length !== 1 ? "s" : ""}`;
            actions.appendChild(count);

            const expandBtn = document.createElement("button");
            expandBtn.className = "functoweb-copy-btn";
            expandBtn.innerHTML = EXPAND_SVG;
            expandBtn.title = "View full size";
            expandBtn.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                openTableOverlay(headers, rows);
            });
            actions.appendChild(expandBtn);

            const csv = tableToCsv(headers, rows);
            actions.appendChild(makeDownloadButton(csv, "table.csv"));
            actions.appendChild(makeCopyButton(csv));

            body.appendChild(actions);

            enhanceTable(table);

            return body;
        },

        download(payload) {
            const body = document.createElement("div");
            body.className = "functoweb-result-body functoweb-result-download";

            const btn = document.createElement("a");
            btn.className = "functoweb-download-btn";
            btn.href = `/download/${payload.file_id}`;
            btn.download = payload.filename;
            btn.innerHTML = `${DOWNLOAD_SVG} ${payload.filename}`;

            body.appendChild(btn);
            return body;
        },

        downloads(payload) {
            const files = Array.isArray(payload.files) ? payload.files : [];

            const body = document.createElement("div");
            body.className = "functoweb-result-body functoweb-result-downloads";

            for (const f of files) {
                const btn = document.createElement("a");
                btn.className = "functoweb-download-btn";
                btn.href = `/download/${f.file_id}`;
                btn.download = f.filename;
                btn.innerHTML = `${DOWNLOAD_SVG} ${f.filename}`;
                body.appendChild(btn);
            }

            return body;
        },
    };

    let _container = null;
    let _parentEl = null;

    function init(parentElement) {
        _parentEl = parentElement;
    }

    function getOrCreateContainer() {
        if (!_container) {
            _container = document.createElement("div");
            _container.className = "functoweb-result-container";
            _parentEl.appendChild(_container);
        }
        return _container;
    }

    function clearContainer() {
        const container = getOrCreateContainer();
        container.innerHTML = "";
        return container;
    }

    function renderResult(isError, type, payload) {
        const container = getOrCreateContainer();

        if (type === "multiple") {
            const items = Array.isArray(payload) ? payload : payload?.data;
            if (Array.isArray(items)) {
                for (const item of items) {
                    renderResult(false, item.type || "text", item);
                }
                return;
            }
        }

        const variant = isError ? "error" : "success";
        const block = makeBlock(variant);

        if (isError) {
            block.appendChild(makeLabel("Error"));
        }

        const renderer = renderers[type] || renderers.text;
        if (!renderers[type]) {
            console.warn(`[functoweb] Unknown result type: "${type}", falling back to text`);
        }
        block.appendChild(renderer(payload));

        container.appendChild(block);
    }

    window.functoweb = window.functoweb || {};
    window.functoweb.result = { init, getOrCreateContainer, clearContainer, renderResult };
})();