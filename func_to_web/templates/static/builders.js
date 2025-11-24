// ============================================================================
// BUILDERS.JS - DOM Construction (Pure creation, no side effects)
// ============================================================================

// ===== INPUT BUILDERS =====

function createListInput(fieldType, defaultValue) {
    let input;
    
    if (fieldType === 'select') {
        input = document.createElement('select');
    } else if (fieldType === 'checkbox') {
        input = document.createElement('input');
        input.type = 'checkbox';
        if (defaultValue !== null) {
            input.checked = defaultValue === true || defaultValue === 'true';
        }
    } else if (fieldType === 'color') {
        input = document.createElement('input');
        input.type = 'color';
        input.value = normalizeColorValue(defaultValue);
    } else {
        input = document.createElement('input');
        input.type = fieldType;
        if (defaultValue !== null) {
            input.value = defaultValue;
        }
    }
    
    return input;
}

function applyInputConstraints(input, constraints) {
    if (constraints.min !== undefined) input.min = constraints.min;
    if (constraints.max !== undefined) input.max = constraints.max;
    if (constraints.step !== undefined) input.step = constraints.step;
    if (constraints.minlength !== undefined) input.minLength = constraints.minlength;
    if (constraints.maxlength !== undefined) input.maxLength = constraints.maxlength;
    if (constraints.pattern !== undefined) input.pattern = constraints.pattern;
    if (constraints.required && constraints.fieldType !== 'checkbox') {
        input.required = true;
    }
}

// ===== BUTTON BUILDERS =====

function createListButton(type, isDisabled) {
    const button = document.createElement('button');
    button.type = 'button';
    button.disabled = isDisabled;
    
    if (type === 'add') {
        button.className = 'list-btn list-btn-add';
        button.textContent = '+';
    } else {
        button.className = 'list-btn list-btn-remove';
        button.textContent = '−';
    }
    
    return button;
}

// ===== ERROR DIV BUILDER =====

function createErrorDiv(inputName) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'list-item-error';
    errorDiv.id = generateErrorId(inputName);
    errorDiv.style.display = 'none';
    return errorDiv;
}

// ===== COMPLETE LIST ITEM BUILDER =====

function createListItemElement(fieldName, fieldType, index, config) {
    const { isDisabled = false, defaultValue = null, constraints = {} } = config;
    
    const itemWrapper = document.createElement('div');
    itemWrapper.className = 'list-item-wrapper';
    
    const itemDiv = document.createElement('div');
    itemDiv.className = 'list-item';
    
    const input = createListInput(fieldType, defaultValue);
    input.name = generateListItemName(fieldName, index);
    input.disabled = isDisabled;
    
    applyInputConstraints(input, { ...constraints, fieldType });
    
    const errorDiv = createErrorDiv(input.name);
    const removeBtn = createListButton('remove', isDisabled);
    const addBtn = createListButton('add', isDisabled);
    
    itemDiv.appendChild(input);
    itemDiv.appendChild(removeBtn);
    itemDiv.appendChild(addBtn);
    
    itemWrapper.appendChild(itemDiv);
    itemWrapper.appendChild(errorDiv);
    
    return itemWrapper;
}

// ===== RESULT DISPLAY BUILDERS =====

function createImageResult(imageSrc) {
    const img = document.createElement('img');
    img.src = imageSrc;
    img.alt = 'Result';
    return img;
}

function createFileDownloadElement(fileId, filename) {
    const container = document.createElement('div');
    container.className = 'file-download';
    
    const fileNameSpan = document.createElement('span');
    fileNameSpan.className = 'file-name';
    fileNameSpan.textContent = `📄 ${filename}`;
    
    const downloadBtn = document.createElement('button');
    downloadBtn.textContent = 'Download';
    downloadBtn.onclick = () => downloadFile(fileId, filename);
    
    container.appendChild(fileNameSpan);
    container.appendChild(downloadBtn);
    
    return container;
}

function createMultipleFilesDownload(files) {
    const container = document.createElement('div');
    container.className = 'files-download';
    
    const title = document.createElement('h3');
    title.textContent = 'Files ready:';
    container.appendChild(title);
    
    files.forEach(file => {
        const fileElement = createFileDownloadElement(file.file_id, file.filename);
        container.appendChild(fileElement);
    });
    
    return container;
}

function createJsonResult(data) {
    const container = document.createElement('div');
    container.className = 'result-json-container';
    
    const displayText = typeof data === 'string' 
        ? data 
        : JSON.stringify(data, null, 2);

    const pre = document.createElement('pre');
    pre.textContent = displayText;
    
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    
    const copyIconSvg = `
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
    `;
    
    const checkIconSvg = `
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
    `;

    copyBtn.innerHTML = copyIconSvg;
    copyBtn.setAttribute('aria-label', 'Copy to clipboard');
    copyBtn.title = "Copy to clipboard";
    
    let resetTimer = null;

    copyBtn.onclick = () => {
        copyToClipboard(displayText);
        
        copyBtn.innerHTML = checkIconSvg;
        
        if (resetTimer) clearTimeout(resetTimer);
        
        resetTimer = setTimeout(() => {
            copyBtn.innerHTML = copyIconSvg;
            resetTimer = null;
        }, 2000);
    };
    
    container.appendChild(copyBtn);
    container.appendChild(pre);
    
    return container;
}

function createResultElement(data) {
    if (data.result_type === 'image') {
        return createImageResult(data.result);
    }
    
    if (data.result_type === 'download') {
        return createFileDownloadElement(data.file_id, data.filename);
    }
    
    if (data.result_type === 'downloads') {
        return createMultipleFilesDownload(data.files);
    }
    
    if (data.result_type === 'multiple') {
        return createMultipleOutputs(data.outputs);
    }

    if (data.result_type === 'table') {
        return createTableResult(data.headers, data.rows);
    }
    
    return createJsonResult(data.result);
}

function extractListConfig(container) {
    return {
        min: container.dataset.listMin || undefined,
        max: container.dataset.listMax || undefined,
        step: container.dataset.listStep || undefined,
        minlength: container.dataset.listMinlength || undefined,
        maxlength: container.dataset.listMaxlength || undefined,
        pattern: container.dataset.listPattern || undefined,
        required: container.dataset.listRequired === 'true'
    };
}

function createMultipleOutputs(outputs) {
    const container = document.createElement('div');
    container.className = 'multiple-outputs';
    
    outputs.forEach(output => {
        const wrapper = document.createElement('div');
        wrapper.className = 'output-item';
        
        const element = createResultElement(output);
        wrapper.appendChild(element);
        container.appendChild(wrapper);
    });
    
    return container;
}

// ===== TABLE BUILDER =====

function createTableResult(headers, rows) {
    const container = document.createElement('div');
    container.className = 'result-table-container';
    
    const table = document.createElement('table');
    table.className = 'result-table';
    
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    rows.forEach(row => {
        const tr = document.createElement('tr');
        row.forEach(cell => {
            const td = document.createElement('td');
            td.textContent = cell;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    
    container.appendChild(table);
    return container;
}