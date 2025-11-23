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
    
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify(data, null, 2);
    
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = 'Copy';
    copyBtn.onclick = () => copyToClipboard(JSON.stringify(data, null, 2));
    
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