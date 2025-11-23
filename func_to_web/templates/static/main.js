(function() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;
    
    const html = document.documentElement;
    
    // Cargar tema guardado o usar 'light' por defecto
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', savedTheme);
    
    // Toggle theme al hacer click
    themeToggle.addEventListener('click', () => {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
})();

let form, resultDiv, errorDiv, submitBtn, loadingOverlay, loadingTitle, progressBar, progressText;

// ===== DOM MANIPULATION HELPERS =====

function disableFieldAndClearValidation(field) {
    field.disabled = true;
    field.removeAttribute('required');
    field.required = false;
    field.classList.remove('was-validated');
}

function enableFieldAndSetRequired(field) {
    field.disabled = false;
    field.setAttribute('required', 'required');
    field.required = true;
}

function updateColorFieldValue(field) {
    const normalized = normalizeColorValue(field.value);
    field.value = normalized;
    const preview = document.querySelector(`[data-color-preview="${field.name}"]`);
    const picker = document.querySelector(`[data-color-picker="${field.name}"]`);
    if (preview) preview.style.backgroundColor = normalized;
    if (picker) picker.value = normalized;
}

function disableListContainer(container) {
    container.dataset.disabled = 'true';
    container.querySelectorAll('.list-item-error').forEach(el => hideValidationError(el));
    container.querySelectorAll('input, select').forEach(el => {
        el.disabled = true;
        el.classList.remove('was-validated');
    });
    container.querySelectorAll('button').forEach(el => el.disabled = true);
}

function enableListContainer(container) {
    container.dataset.disabled = 'false';
    container.querySelectorAll('input, select').forEach(el => el.disabled = false);
    container.querySelectorAll('button').forEach(el => el.disabled = false);
}

function populateListContainer(container, fieldName) {
    if (container.children.length === 0) {
        const fieldType = container.dataset.listType;
        const defaultValue = container.dataset.listDefault;
        const minLength = parseIntOrDefault(container.dataset.listContainerMin, 0);
        const defaults = parseListDefaults(defaultValue);
        const itemsToCreate = calculateItemsToCreate(defaults, minLength);
        
        if (defaults.length > 0) {
            defaults.forEach(defaultVal => {
                addListItem(container, fieldName, fieldType, false, defaultVal);
            });
        }
        
        for (let i = 0; i < itemsToCreate; i++) {
            addListItem(container, fieldName, fieldType, false);
        }
    } else {
        enableListContainer(container);
    }
}

function setColorPickerEnabled(picker, enabled) {
    if (picker) picker.disabled = !enabled;
}

function setColorPreviewEnabled(preview, enabled) {
    if (!preview) return;
    if (enabled) {
        preview.classList.remove('disabled');
        preview.style.pointerEvents = 'auto';
    } else {
        preview.classList.add('disabled');
        preview.style.pointerEvents = 'none';
    }
}

function syncColorInputs(input, preview, picker, value) {
    input.value = value;
    preview.style.backgroundColor = value;
    picker.value = value;
}

function showError(message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    resultDiv.style.display = 'none';
}

function hideErrors() {
    errorDiv.style.display = 'none';
    resultDiv.style.display = 'none';
}

// ===== INITIALIZATION =====

function initializeForm(submitUrl) {
    form = document.getElementById('form');
    resultDiv = document.getElementById('result');
    errorDiv = document.getElementById('error');
    submitBtn = document.getElementById('submitBtn');
    loadingOverlay = document.getElementById('loadingOverlay');
    loadingTitle = document.getElementById('loadingTitle');
    progressBar = document.getElementById('progressBar');
    progressText = document.getElementById('progressText');
    
    setupColorInputs();
    setupOptionalToggles();
    setupListFields();
    setupValidation();
    setupFormSubmit(submitUrl);
    setupKeyboardShortcuts();
    
    // Auto-focus first field
    const firstInput = form.querySelector('input:not([type="checkbox"]):not([type="hidden"]):not(.color-picker-hidden), select');
    if (firstInput && !firstInput.disabled) {
        firstInput.focus();
    }
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl+Enter or Cmd+Enter to submit
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            if (!submitBtn.disabled) {
                form.requestSubmit();
            }
        }
    });
}

function downloadFile(fileId, filename) {
    const a = document.createElement('a');
    a.href = `/download/${fileId}`;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function setLoading(show, title = 'Uploading...') {
    if (show) {
        loadingOverlay.classList.add('active');
        loadingTitle.textContent = title;
        submitBtn.disabled = true;
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
    } else {
        loadingOverlay.classList.remove('active');
        submitBtn.disabled = false;
    }
}

function updateProgress(percent) {
    progressBar.style.width = percent + '%';
    progressText.textContent = Math.round(percent) + '%';
}

function getFileSize() {
    const fileInput = form.querySelector('input[type="file"]');
    return fileInput && fileInput.files.length > 0 ? fileInput.files[0].size : 0;
}

function setupListFields() {
    document.querySelectorAll('[data-list]').forEach(container => {
        const fieldName = container.dataset.list;
        const fieldType = container.dataset.listType;
        const defaultValue = container.dataset.listDefault;
        const minLength = parseIntOrDefault(container.dataset.listContainerMin, 0);
        
        const toggle = document.querySelector(`[data-optional-toggle="${fieldName}"]`);
        const isOptionalField = toggle !== null;
        const isEnabled = !isOptionalField || toggle.checked;
        
        const defaults = parseListDefaults(defaultValue);
        const itemsToCreate = calculateItemsToCreate(defaults, minLength);
        
        if (defaults.length > 0) {
            defaults.forEach(defaultVal => {
                addListItem(container, fieldName, fieldType, !isEnabled, defaultVal);
            });
            
            for (let i = 0; i < itemsToCreate; i++) {
                addListItem(container, fieldName, fieldType, !isEnabled);
            }
        } else {
            for (let i = 0; i < itemsToCreate; i++) {
                addListItem(container, fieldName, fieldType, !isEnabled);
            }
        }
        
        container.dataset.disabled = !isEnabled ? 'true' : 'false';
    });
}

function addListItem(container, fieldName, fieldType, isDisabled = false, defaultValue = null) {
    if (container.dataset.disabled === 'true') isDisabled = true;
    
    const index = container.children.length;
    const maxLength = parseIntOrDefault(container.dataset.listContainerMax, 0);
    
    if (maxLength > 0 && index >= maxLength) return;
    
    const constraints = extractListConfig(container);
    const itemWrapper = createListItemElement(fieldName, fieldType, index, {
        isDisabled,
        defaultValue,
        constraints
    });
    
    const input = itemWrapper.querySelector('input, select');
    const removeBtn = itemWrapper.querySelector('.list-btn-remove');
    const addBtn = itemWrapper.querySelector('.list-btn-add');
    
    input.addEventListener('blur', () => validateField(input));
    input.addEventListener('input', () => {
        if (input.classList.contains('was-validated')) validateField(input);
    });
    
    removeBtn.onclick = () => removeListItem(itemWrapper, container, fieldName);
    addBtn.onclick = () => addListItem(container, fieldName, fieldType);
    
    container.appendChild(itemWrapper);
    updateListButtons(container);
}

function removeListItem(itemWrapper, container, fieldName) {
    const isRequired = container.dataset.listRequired === 'true';
    const isDisabled = container.dataset.disabled === 'true';
    const minLength = parseIntOrDefault(container.dataset.listContainerMin, 0);
    
    if (!canRemoveListItem(container.children.length, minLength, isRequired, isDisabled)) {
        return;
    }
    
    itemWrapper.remove();
    updateListButtons(container);
    reindexListItems(container, fieldName);
}

function updateListButtons(container) {
    const wrappers = container.querySelectorAll('.list-item-wrapper');
    const isRequired = container.dataset.listRequired === 'true';
    const isDisabled = container.dataset.disabled === 'true';
    const minLength = parseIntOrDefault(container.dataset.listContainerMin, 0);
    const maxLength = parseIntOrDefault(container.dataset.listContainerMax, 0);
    
    wrappers.forEach((wrapper, index) => {
        const item = wrapper.querySelector('.list-item');
        const addBtn = item.querySelector('.list-btn-add');
        const removeBtn = item.querySelector('.list-btn-remove');
        
        if (isDisabled) {
            addBtn.style.display = 'none';
            removeBtn.style.display = 'none';
            return;
        }
        
        addBtn.style.display = shouldShowAddButton(index, wrappers.length, maxLength) ? 'flex' : 'none';
        removeBtn.style.display = shouldShowRemoveButton(wrappers.length, minLength, isRequired, isDisabled) ? 'flex' : 'none';
    });
}

function reindexListItems(container, fieldName) {
    const wrappers = container.querySelectorAll('.list-item-wrapper');
    wrappers.forEach((wrapper, index) => {
        const item = wrapper.querySelector('.list-item');
        const input = item.querySelector('input, select');
        const errorDiv = wrapper.querySelector('.list-item-error');
        
        input.name = generateListItemName(fieldName, index);
        if (errorDiv) {
            errorDiv.id = generateErrorId(input.name);
        }
    });
}

function setupOptionalToggles() {
    document.querySelectorAll('[data-optional-toggle]').forEach(toggle => {
        const fieldName = toggle.dataset.optionalToggle;
        const field = document.getElementById(fieldName);
        const listContainer = document.querySelector(`[data-list="${fieldName}"]`);
        const colorPicker = document.querySelector(`[data-color-picker="${fieldName}"]`);
        const colorPreview = document.querySelector(`[data-color-preview="${fieldName}"]`);
        
        function updateFieldState() {
            const isEnabled = toggle.checked;
            
            if (field) {
                if (isEnabled) {
                    enableFieldAndSetRequired(field);
                    if (field.dataset.colorInput !== undefined) {
                        updateColorFieldValue(field);
                    }
                } else {
                    disableFieldAndClearValidation(field);
                    hideValidationError(document.getElementById(generateErrorId(field.name)));
                }
            }
            
            if (listContainer) {
                if (isEnabled) {
                    populateListContainer(listContainer, fieldName);
                    updateListButtons(listContainer);
                } else {
                    disableListContainer(listContainer);
                    if (listContainer.children.length === 0) {
                        const fieldType = listContainer.dataset.listType;
                        addListItem(listContainer, fieldName, fieldType, true);
                    }
                }
            }
            
            setColorPickerEnabled(colorPicker, isEnabled);
            setColorPreviewEnabled(colorPreview, isEnabled);
        }
        
        toggle.addEventListener('change', updateFieldState);
        if (field || colorPicker || colorPreview) {
            updateFieldState();
        }
    });
}

function setupColorInputs() {
    document.querySelectorAll('[data-color-input]').forEach(input => {
        const preview = document.querySelector(`[data-color-preview="${input.name}"]`);
        const picker = document.querySelector(`[data-color-picker="${input.name}"]`);
        
        if (!preview || !picker) return;
        
        input.addEventListener('input', (e) => {
            const value = e.target.value;
            if (isValidColor(value)) {
                preview.style.backgroundColor = value;
                picker.value = expandShortHex(value);
            }
        });
        
        preview.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (!preview.classList.contains('disabled') && !picker.disabled) {
                picker.click();
            }
        });
        
        const syncFromPicker = (e) => {
            syncColorInputs(input, preview, picker, e.target.value);
            if (input.classList.contains('was-validated')) {
                validateField(input);
            }
        };
        
        picker.addEventListener('input', syncFromPicker);
        picker.addEventListener('change', syncFromPicker);
    });
}

function setupValidation() {
    form.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('blur', () => validateField(input));
        input.addEventListener('input', () => {
            if (input.classList.contains('was-validated')) validateField(input);
        });
    });
}

function validateField(input) {
    const errorEl = document.getElementById(generateErrorId(input.name));
    if (!errorEl) return true;
    
    if (input.disabled) {
        hideValidationError(errorEl);
        return true;
    }
    
    input.classList.add('was-validated');
    
    const value = input.value || '';
    const result = validateFieldValue(input, value);
    
    showValidationError(errorEl, result);
    return result.valid;
}

function setupFormSubmit(submitUrl) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        let isValid = true;
        
        form.querySelectorAll('input:not([type="checkbox"]):not(.color-picker-hidden):not(:disabled), select:not(:disabled)').forEach(input => {
            if (input.dataset.colorInput !== undefined && !input.disabled) {
                const value = input.value || '';
                const isRequired = input.hasAttribute('required');
                const result = validateColorField(value, isRequired);
                
                if (!result.valid) {
                    const errorEl = document.getElementById(generateErrorId(input.name));
                    if (errorEl) {
                        showValidationError(errorEl, result);
                    }
                    input.classList.add('was-validated');
                    isValid = false;
                    return;
                }
            }
            
            if (!validateField(input)) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            showError('Please fix the errors above');
            return;
        }
        
        document.querySelectorAll('[data-list]').forEach(container => {
            const fieldName = container.dataset.list;
            const fieldType = container.dataset.listType;
            
            const result = validateListContainer(container, fieldName, fieldType);
            
            if (!result.valid) {
                isValid = false;
                showError(result.error);
            }
        });
        
        if (!isValid) {
            return;
        }
        
        hideErrors();
        
        const fileSize = getFileSize();
        const loadingMsg = formatUploadMessage(fileSize);
        
        setLoading(true, loadingMsg);
        
        try {
            const formData = new FormData(form);
            
            document.querySelectorAll('[data-list]').forEach(container => {
                const fieldName = container.dataset.list;
                const fieldType = container.dataset.listType;
                
                const keysToRemove = [];
                for (let key of formData.keys()) {
                    if (key.startsWith(`${fieldName}[`)) {
                        keysToRemove.push(key);
                    }
                }
                keysToRemove.forEach(key => formData.delete(key));
                
                const wrappers = container.querySelectorAll('.list-item-wrapper');
                const listValues = extractListValues(wrappers, fieldType);
                
                formData.set(fieldName, JSON.stringify(listValues));
            });
            
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = formatProgressPercent(e.loaded, e.total);
                    updateProgress(percent);
                    if (fileSize > 0) {
                        loadingTitle.textContent = formatProgressMessage(e.loaded, e.total);
                    }
                }
            });
            
            xhr.addEventListener('loadstart', () => setLoading(true, loadingMsg));
            
            xhr.addEventListener('readystatechange', () => {
                if (xhr.readyState === 3) {
                    loadingTitle.textContent = 'Processing...';
                    progressBar.style.width = '100%';
                    progressText.textContent = '100%';
                }
            });
            
            xhr.addEventListener('load', () => {
                setLoading(false);
                try {
                    const data = JSON.parse(xhr.responseText);
                    if (data.success) {
                        displayResult(data);
                    } else {
                        showError('Error: ' + data.error);
                    }
                } catch (parseError) {
                    showError('Error: Invalid server response');
                }
            });
            
            xhr.addEventListener('error', () => {
                setLoading(false);
                showError('Error: Network error');
            });
            
            xhr.addEventListener('abort', () => {
                setLoading(false);
                showError('Upload cancelled');
            });
            
            xhr.addEventListener('timeout', () => {
                setLoading(false);
                showError('Error: Request timeout');
            });
            
            xhr.open('POST', submitUrl);
            xhr.send(formData);
            
        } catch (err) {
            setLoading(false);
            showError('Error: ' + err.message);
        }
    });
}

function displayResult(data) {
    resultDiv.innerHTML = '';
    const resultElement = createResultElement(data);
    resultDiv.appendChild(resultElement);
    resultDiv.style.display = 'block';
}