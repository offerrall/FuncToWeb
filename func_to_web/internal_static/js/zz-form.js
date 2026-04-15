(function() {
    const form = document.querySelector("pti-form");
    if (!form) return;

    const action = form.dataset.action;
    const { getOrCreateContainer, clearContainer, renderResult } = window.functoweb.result;

    window.functoweb.result.init(form.parentElement);

    form.addEventListener("reset", () => {
        clearContainer();
    });

    /* ── SVG Icons ── */

    const ICONS = {
        chevron: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`,
    };

    /* ── Console output (prints) ── */

    function createConsole() {
        const wrapper = document.createElement("div");
        wrapper.className = "functoweb-console";

        const toggle = document.createElement("button");
        toggle.className = "functoweb-console-toggle";
        toggle.innerHTML = `${ICONS.chevron} <span>Progress</span> <span class="functoweb-console-count">0</span>`;
        wrapper.appendChild(toggle);

        const content = document.createElement("div");
        content.className = "functoweb-console-content";

        const pre = document.createElement("pre");
        pre.className = "functoweb-console-log";
        content.appendChild(pre);
        wrapper.appendChild(content);

        let open = true;
        wrapper.classList.add("open");
        toggle.addEventListener("click", () => {
            open = !open;
            wrapper.classList.toggle("open", open);
        });

        let pending = [];
        let rafId = null;
        let lineCount = 0;

        function flush() {
            if (!pending.length) return;
            pre.textContent += pending.join("\n") + "\n";
            lineCount += pending.length;
            toggle.querySelector(".functoweb-console-count").textContent = lineCount;
            pre.scrollTop = pre.scrollHeight;
            pending = [];
            rafId = null;
        }

        return {
            el: wrapper,
            append(lines) {
                pending.push(...(Array.isArray(lines) ? lines : [lines]));
                if (!rafId) {
                    rafId = requestAnimationFrame(flush);
                }
            },
        };
    }

    /* ── SSE parser (shared between fetch and XHR) ── */

    function createSSEContext(onStart) {
        const container = clearContainer();

        let consoleUI = null;
        let buffer = "";

        function process(text) {
            buffer += text;
            const parts = buffer.split("\n\n");
            buffer = parts.pop();

            for (const part of parts) {
                const eventMatch = part.match(/^event:\s*(.+)$/m);
                const dataMatch = part.match(/^data:\s*(.+)$/m);
                if (!eventMatch || !dataMatch) continue;

                const event = eventMatch[1].trim();
                const data = JSON.parse(dataMatch[1]);

                if (event === "start") {
                    if (typeof onStart === "function") onStart();
                } else if (event === "print") {
                    if (!consoleUI) {
                        consoleUI = createConsole();
                        container.appendChild(consoleUI.el);
                    }
                    consoleUI.append(data);
                } else if (event === "result") {
                    if (data.success) {
                        renderResult(false, data.type || "text", data);
                    } else {
                        renderResult(true, "text", data);
                    }
                }
            }
        }

        return { process };
    }

    /* ── SSE stream reader (for fetch responses) ── */

    function readSSE(response) {
        const ctx = createSSEContext();
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        async function pump() {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                ctx.process(decoder.decode(value, { stream: true }));
            }
            ctx.process("\n\n");
        }

        pump().catch(err => {
            renderResult(true, "text", { data: "Stream failed: " + err.message });
        });
    }

    /* ── File helpers ── */

    function hasFiles(detail) {
        for (const v of Object.values(detail)) {
            if (v instanceof File) return true;
            if (Array.isArray(v) && v.some(item => item instanceof File)) return true;
        }
        return false;
    }

    function getTotalFileSize(detail) {
        let total = 0;
        for (const v of Object.values(detail)) {
            if (v instanceof File) total += v.size;
            if (Array.isArray(v)) v.forEach(item => { if (item instanceof File) total += item.size; });
        }
        return total;
    }

    function formatSize(bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    }

    /* ── Upload overlay ── */

    function showOverlay(totalSize) {
        let overlay = document.querySelector(".functoweb-upload-overlay");
        if (!overlay) {
            overlay = document.createElement("div");
            overlay.className = "functoweb-upload-overlay";
            overlay.innerHTML = `
                <div class="functoweb-upload-modal">
                    <h2 class="functoweb-upload-title">Uploading files...</h2>
                    <div class="functoweb-progress-bar">
                        <div class="functoweb-progress-fill"></div>
                    </div>
                    <div class="functoweb-progress-text">
                        <span id="progress-percent">0%</span>
                        <span id="progress-size">0 B / ${formatSize(totalSize)}</span>
                    </div>
                </div>`;
            document.body.appendChild(overlay);
        } else {
            overlay.classList.remove("hidden");
            overlay.querySelector(".functoweb-progress-fill").style.width = "0%";
            overlay.querySelector("#progress-percent").textContent = "0%";
            overlay.querySelector("#progress-size").textContent = `0 B / ${formatSize(totalSize)}`;
        }
        return overlay;
    }

    function updateProgress(overlay, loaded, total) {
        const percent = Math.round((loaded / total) * 100);
        overlay.querySelector(".functoweb-progress-fill").style.width = percent + "%";
        overlay.querySelector("#progress-percent").textContent = percent + "%";
        overlay.querySelector("#progress-size").textContent = `${formatSize(loaded)} / ${formatSize(total)}`;
        if (percent >= 100) {
            overlay.querySelector(".functoweb-upload-title").textContent = "Processing...";
        }
    }

    function hideOverlay(overlay) {
        overlay.classList.add("hidden");
    }

    /* ── Form submit ── */

    form.addEventListener("submit", async (e) => {
        const formData = new FormData();
        const values = {};

        for (const [k, v] of Object.entries(e.detail)) {
            if (v instanceof File) {
                formData.append(k, v);
            } else if (Array.isArray(v) && v.some(item => item instanceof File)) {
                for (const file of v) formData.append(k, file);
            } else {
                values[k] = v;
            }
        }
        formData.append("values", JSON.stringify(values));

        if (hasFiles(e.detail)) {
            const totalSize = getTotalFileSize(e.detail);
            const overlay = showOverlay(totalSize);

            const xhr = new XMLHttpRequest();
            xhr.open("POST", action);
            xhr.responseType = "text";

            let uploadDone = false;
            let responseText = "";

            xhr.upload.addEventListener("progress", (ev) => {
                if (ev.lengthComputable) updateProgress(overlay, ev.loaded, ev.total);
            });

            xhr.upload.addEventListener("load", () => {
                uploadDone = true;
            });

            xhr.addEventListener("progress", () => {
                const text = xhr.responseText.slice(responseText.length);
                responseText = xhr.responseText;
                if (uploadDone && text) {
                    processSSEText(text);
                }
            });

            xhr.addEventListener("load", () => {
                hideOverlay(overlay);
                const remaining = xhr.responseText.slice(responseText.length);
                if (remaining) processSSEText(remaining);
                processSSEText("\n\n");
            });

            xhr.addEventListener("error", () => {
                hideOverlay(overlay);
                renderResult(true, "text", { data: "Upload failed — network error" });
            });

            const ctx = createSSEContext(() => hideOverlay(overlay));
            function processSSEText(text) { ctx.process(text); }

            xhr.send(formData);
        } else {
            try {
                const res = await fetch(action, { method: "POST", body: formData });
                readSSE(res);
            } catch (err) {
                renderResult(true, "text", { data: "Request failed: " + err.message });
            }
        }
    });
})();