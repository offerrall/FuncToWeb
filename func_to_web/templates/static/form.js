(function() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = themeToggle?.querySelector('.theme-icon');
    
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    if (themeIcon) themeIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
    
    themeToggle?.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        if (themeIcon) themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
    });
})();

let form, resultDiv, errorDiv, submitBtn, loadingOverlay, loadingTitle, progressBar, progressText;

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

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function setupListFields() {
    document.querySelectorAll('[data-list]').forEach(container => {
        const fieldName = container.dataset.list;
        const fieldType = container.dataset.listType;
        const defaultValue = container.dataset.listDefault;
        const minLength = parseInt(container.dataset.listContainerMin) || 0;
        
        const toggle = document.querySelector(`[data-optional-toggle="${fieldName}"]`);
        const isOptionalField = toggle !== null;
        const isEnabled = !isOptionalField || toggle.checked;
        
        let defaults = [];
        if (defaultValue && defaultValue !== 'null' && defaultValue !== '[]') {
            try {
                defaults = JSON.parse(defaultValue);
                if (!Array.isArray(defaults)) defaults = [];
            } catch (e) {
                defaults = [];
            }
        }
        
        if (defaults.length > 0) {
            defaults.forEach(defaultVal => {
                addListItem(container, fieldName, fieldType, !isEnabled, defaultVal);
            });
            
            if (minLength > defaults.length) {
                const itemsToCreate = minLength - defaults.length;
                for (let i = 0; i < itemsToCreate; i++) {
                    addListItem(container, fieldName, fieldType, !isEnabled);
                }
            }
        } else {
            const itemsToCreate = minLength > 0 ? minLength : 1;
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
    
    const maxLength = container.dataset.listContainerMax;
    if (maxLength && parseInt(maxLength) > 0 && index >= parseInt(maxLength)) {
        return;
    }
    
    const itemWrapper = document.createElement('div');
    itemWrapper.className = 'list-item-wrapper';
    
    const itemDiv = document.createElement('div');
    itemDiv.className = 'list-item';
    
    let input;
    if (fieldType === 'select') {
        input = document.createElement('select');
    } else if (fieldType === 'checkbox') {
        input = document.createElement('input');
        input.type = 'checkbox';
        if (defaultValue !== null) input.checked = defaultValue === true || defaultValue === 'true';
    } else if (fieldType === 'color') {
        input = document.createElement('input');
        input.type = 'color';
        input.value = defaultValue !== null ? defaultValue : '#000000';
    } else {
        input = document.createElement('input');
        input.type = fieldType;
        if (defaultValue !== null) input.value = defaultValue;
    }
    
    input.name = `${fieldName}[${index}]`;
    input.disabled = isDisabled;
    
    if (container.dataset.listMin) input.min = container.dataset.listMin;
    if (container.dataset.listMax) input.max = container.dataset.listMax;
    if (container.dataset.listStep) input.step = container.dataset.listStep;
    if (container.dataset.listMinlength) input.minLength = container.dataset.listMinlength;
    if (container.dataset.listMaxlength) input.maxLength = container.dataset.listMaxlength;
    if (container.dataset.listPattern) input.pattern = container.dataset.listPattern;
    if (container.dataset.listRequired === 'true' && fieldType !== 'checkbox') input.required = true;
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'list-item-error';
    errorDiv.id = `error-${input.name}`;
    errorDiv.style.display = 'none';
    
    input.addEventListener('blur', () => validateField(input));
    input.addEventListener('input', () => {
        if (input.classList.contains('was-validated')) validateField(input);
    });
    
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'list-btn list-btn-remove';
    removeBtn.textContent = '−';
    removeBtn.disabled = isDisabled;
    removeBtn.onclick = () => removeListItem(itemWrapper, container, fieldName);
    
    const addBtn = document.createElement('button');
    addBtn.type = 'button';
    addBtn.className = 'list-btn list-btn-add';
    addBtn.textContent = '+';
    addBtn.disabled = isDisabled;
    addBtn.onclick = () => addListItem(container, fieldName, fieldType);
    
    itemDiv.appendChild(input);
    itemDiv.appendChild(removeBtn);
    itemDiv.appendChild(addBtn);
    
    itemWrapper.appendChild(itemDiv);
    itemWrapper.appendChild(errorDiv);
    
    container.appendChild(itemWrapper);
    
    updateListButtons(container);
}

function removeListItem(itemWrapper, container, fieldName) {
    const isRequired = container.dataset.listRequired === 'true';
    const isDisabled = container.dataset.disabled === 'true';
    const minLength = parseInt(container.dataset.listContainerMin) || 0;
    
    if (minLength > 0 && container.children.length <= minLength && !isDisabled) {
        return;
    }
    
    if (isRequired && !isDisabled && container.children.length <= 1) {
        return;
    }
    
    if (container.children.length > 1 || (!isRequired || isDisabled)) {
        itemWrapper.remove();
        updateListButtons(container);
        reindexListItems(container, fieldName);
    }
}

function updateListButtons(container) {
    const wrappers = container.querySelectorAll('.list-item-wrapper');
    const isRequired = container.dataset.listRequired === 'true';
    const isDisabled = container.dataset.disabled === 'true';
    const minLength = parseInt(container.dataset.listContainerMin) || 0;
    const maxLength = parseInt(container.dataset.listContainerMax) || 0;
    
    wrappers.forEach((wrapper, index) => {
        const item = wrapper.querySelector('.list-item');
        const addBtn = item.querySelector('.list-btn-add');
        const removeBtn = item.querySelector('.list-btn-remove');
        
        if (isDisabled) {
            addBtn.style.display = 'none';
            removeBtn.style.display = 'none';
            return;
        }
        
        const canAddMore = !maxLength || wrappers.length < maxLength;
        addBtn.style.display = (index === wrappers.length - 1 && canAddMore) ? 'flex' : 'none';
        
        const atMinLength = minLength > 0 && wrappers.length <= minLength;
        const atRequiredMin = isRequired && !isDisabled && wrappers.length === 1;
        const canRemove = !atMinLength && !atRequiredMin && wrappers.length > 0;
        
        removeBtn.style.display = canRemove ? 'flex' : 'none';
    });
}

function reindexListItems(container, fieldName) {
    const wrappers = container.querySelectorAll('.list-item-wrapper');
    wrappers.forEach((wrapper, index) => {
        const item = wrapper.querySelector('.list-item');
        const input = item.querySelector('input, select');
        const errorDiv = wrapper.querySelector('.list-item-error');
        
        input.name = `${fieldName}[${index}]`;
        if (errorDiv) {
            errorDiv.id = `error-${input.name}`;
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
                field.disabled = !isEnabled;
                if (!isEnabled) {
                    field.removeAttribute('required');
                    field.required = false;
                    field.classList.remove('was-validated');
                    const errorEl = document.getElementById(`error-${field.name}`);
                    if (errorEl) {
                        errorEl.style.display = 'none';
                        errorEl.textContent = '';
                    }
                } else {
                    field.setAttribute('required', 'required');
                    field.required = true;
                    
                    if (field.dataset.colorInput !== undefined) {
                        const currentValue = field.value || '';
                        const isValidColor = /^#[0-9a-fA-F]{6}$/.test(currentValue) || /^#[0-9a-fA-F]{3}$/.test(currentValue);
                        
                        if (!isValidColor) {
                            field.value = '#000000';
                            const preview = document.querySelector(`[data-color-preview="${field.name}"]`);
                            const picker = document.querySelector(`[data-color-picker="${field.name}"]`);
                            if (preview) preview.style.backgroundColor = '#000000';
                            if (picker) picker.value = '#000000';
                        }
                    }
                }
            }
            
            if (listContainer) {
                const fieldType = listContainer.dataset.listType;
                const defaultValue = listContainer.dataset.listDefault;
                const minLength = parseInt(listContainer.dataset.listContainerMin) || 0;
                
                if (!isEnabled) {
                    listContainer.dataset.disabled = 'true';
                    
                    listContainer.querySelectorAll('.list-item-error').forEach(errorEl => {
                        errorEl.style.display = 'none';
                        errorEl.textContent = '';
                    });
                    
                    listContainer.querySelectorAll('input, select').forEach(el => {
                        el.disabled = true;
                        el.classList.remove('was-validated');
                    });
                    
                    listContainer.querySelectorAll('button').forEach(el => el.disabled = true);
                    
                    if (listContainer.children.length === 0) {
                        addListItem(listContainer, fieldName, fieldType, true);
                    }
                } else {
                    listContainer.dataset.disabled = 'false';
                    
                    if (listContainer.children.length === 0) {
                        let defaults = [];
                        if (defaultValue && defaultValue !== 'null' && defaultValue !== '[]') {
                            try {
                                defaults = JSON.parse(defaultValue);
                                if (!Array.isArray(defaults)) defaults = [];
                            } catch (e) {
                                defaults = [];
                            }
                        }
                        
                        if (defaults.length > 0) {
                            defaults.forEach(defaultVal => {
                                addListItem(listContainer, fieldName, fieldType, false, defaultVal);
                            });
                            
                            const itemsToCreate = minLength - defaults.length;
                            for (let i = 0; i < itemsToCreate; i++) {
                                addListItem(listContainer, fieldName, fieldType, false);
                            }
                        } else {
                            const itemsToCreate = Math.max(minLength, 1);
                            for (let i = 0; i < itemsToCreate; i++) {
                                addListItem(listContainer, fieldName, fieldType, false);
                            }
                        }
                    } else {
                        listContainer.querySelectorAll('input, select').forEach(el => {
                            el.disabled = false;
                        });
                        listContainer.querySelectorAll('button').forEach(el => el.disabled = false);
                    }
                }
                
                updateListButtons(listContainer);
            }
            
            if (colorPicker) colorPicker.disabled = !isEnabled;
            
            if (colorPreview) {
                if (!isEnabled) {
                    colorPreview.classList.add('disabled');
                    colorPreview.style.pointerEvents = 'none';
                } else {
                    colorPreview.classList.remove('disabled');
                    colorPreview.style.pointerEvents = 'auto';
                }
            }
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
            if (/^#[0-9a-fA-F]{6}$/.test(value) || /^#[0-9a-fA-F]{3}$/.test(value)) {
                preview.style.backgroundColor = value;
                picker.value = value.length === 4 ? '#' + value[1] + value[1] + value[2] + value[2] + value[3] + value[3] : value;
            }
        });
        
        preview.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (!preview.classList.contains('disabled') && !picker.disabled) picker.click();
        });
        
        picker.addEventListener('input', (e) => {
            input.value = e.target.value;
            preview.style.backgroundColor = e.target.value;
            if (input.classList.contains('was-validated')) validateField(input);
        });
        
        picker.addEventListener('change', (e) => {
            input.value = e.target.value;
            preview.style.backgroundColor = e.target.value;
            if (input.classList.contains('was-validated')) validateField(input);
        });
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
    const errorEl = document.getElementById(`error-${input.name}`);
    if (!errorEl) return true;
    
    if (input.disabled) {
        errorEl.style.display = 'none';
        return true;
    }
    
    input.classList.add('was-validated');
    
    const value = input.value || '';
    const isEmpty = value.trim() === '';
    
    const isListItem = input.name.includes('[') && input.name.includes(']');
    
    if (isListItem) {
        if (isEmpty && !input.hasAttribute('required')) {
            errorEl.style.display = 'none';
            return true;
        }
        if (isEmpty && input.hasAttribute('required')) {
            errorEl.textContent = 'This field is required';
            errorEl.style.display = 'block';
            return false;
        }
    } else {
        if (input.hasAttribute('required') && isEmpty) {
            errorEl.textContent = 'This field is required';
            errorEl.style.display = 'block';
            return false;
        }
    }
    
    if (!isEmpty) {
        if (input.minLength && value.length < input.minLength) {
            errorEl.textContent = `Minimum length is ${input.minLength} characters`;
            errorEl.style.display = 'block';
            return false;
        }
        
        if (input.maxLength && input.maxLength > 0 && value.length > input.maxLength) {
            errorEl.textContent = `Maximum length is ${input.maxLength} characters`;
            errorEl.style.display = 'block';
            return false;
        }
        
        if (input.pattern && !new RegExp(input.pattern).test(value)) {
            if (input.dataset.colorInput !== undefined) {
                errorEl.textContent = 'Please enter a valid color (#RGB or #RRGGBB)';
            } else if (input.type === 'email') {
                errorEl.textContent = 'Please enter a valid email';
            } else if (input.type === 'file') {
                errorEl.textContent = 'Please select a valid file type';
            } else {
                errorEl.textContent = 'Invalid format';
            }
            errorEl.style.display = 'block';
            return false;
        }
        
        if (input.type === 'email' && !value.includes('@')) {
            errorEl.textContent = 'Please enter a valid email';
            errorEl.style.display = 'block';
            return false;
        }
        
        if (input.type === 'number') {
            const numValue = parseFloat(value);
            if (isNaN(numValue)) {
                errorEl.textContent = 'Please enter a valid number';
                errorEl.style.display = 'block';
                return false;
            }
            if (input.min !== '' && numValue < parseFloat(input.min)) {
                errorEl.textContent = `Minimum value is ${input.min}`;
                errorEl.style.display = 'block';
                return false;
            }
            if (input.max !== '' && numValue > parseFloat(input.max)) {
                errorEl.textContent = `Maximum value is ${input.max}`;
                errorEl.style.display = 'block';
                return false;
            }
        }
    }
    
    if (!isEmpty && !input.validity.valid) {
        if (input.validity.valueMissing) {
            errorEl.textContent = 'This field is required';
        } else if (input.validity.rangeUnderflow) {
            errorEl.textContent = `Minimum value is ${input.min}`;
        } else if (input.validity.rangeOverflow) {
            errorEl.textContent = `Maximum value is ${input.max}`;
        } else if (input.validity.tooShort) {
            errorEl.textContent = `Minimum length is ${input.minLength} characters`;
        } else if (input.validity.tooLong) {
            errorEl.textContent = `Maximum length is ${input.maxLength} characters`;
        } else if (input.validity.stepMismatch) {
            errorEl.textContent = `Value must be a valid number`;
        } else if (input.validity.typeMismatch) {
            errorEl.textContent = input.type === 'email' ? 'Please enter a valid email' : 
                                  input.type === 'url' ? 'Please enter a valid URL' : 'Invalid format';
        } else if (input.validity.patternMismatch) {
            if (input.dataset.colorInput !== undefined) {
                errorEl.textContent = 'Please enter a valid color (#RGB or #RRGGBB)';
            } else if (input.type === 'file') {
                errorEl.textContent = 'Please select a valid file type';
            } else {
                errorEl.textContent = 'Invalid format';
            }
        } else {
            errorEl.textContent = 'Invalid value';
        }
        errorEl.style.display = 'block';
        return false;
    }
    
    errorEl.style.display = 'none';
    return true;
}

function setupFormSubmit(submitUrl) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        let isValid = true;
        
        form.querySelectorAll('input:not([type="checkbox"]):not(.color-picker-hidden):not(:disabled), select:not(:disabled)').forEach(input => {
            if (input.dataset.colorInput !== undefined && !input.disabled) {
                const value = input.value || '';
                const isEmpty = value.trim() === '';
                const isRequired = input.hasAttribute('required');
                
                if ((isEmpty && isRequired) || (!isEmpty && !/^#[0-9a-fA-F]{6}$/.test(value) && !/^#[0-9a-fA-F]{3}$/.test(value))) {
                    const errorEl = document.getElementById(`error-${input.name}`);
                    if (errorEl) {
                        if (isEmpty && isRequired) {
                            errorEl.textContent = 'This field is required';
                        } else {
                            errorEl.textContent = 'Please enter a valid color (#RGB or #RRGGBB)';
                        }
                        errorEl.style.display = 'block';
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
            errorDiv.textContent = 'Please fix the errors above';
            errorDiv.style.display = 'block';
            resultDiv.style.display = 'none';
            return;
        }
        
        document.querySelectorAll('[data-list]').forEach(container => {
            const fieldName = container.dataset.list;
            const isRequired = container.dataset.listRequired === 'true';
            const isDisabled = container.dataset.disabled === 'true';
            
            if (isDisabled) return;
            
            const minLength = parseInt(container.dataset.listContainerMin) || 0;
            const maxLength = parseInt(container.dataset.listContainerMax) || 0;
            
            const wrappers = container.querySelectorAll('.list-item-wrapper');
            
            let validCount = 0;
            
            wrappers.forEach(wrapper => {
                const item = wrapper.querySelector('.list-item');
                const input = item.querySelector('input, select');
                
                if (input.type === 'checkbox') {
                    validCount++;
                    return;
                }
                
                const value = input.value;
                if (value && value.trim() !== '') {
                    validCount++;
                }
            });
            
            if (minLength > 0 && validCount < minLength) {
                isValid = false;
                errorDiv.textContent = `The field "${fieldName}" requires at least ${minLength} item${minLength > 1 ? 's' : ''}`;
                errorDiv.style.display = 'block';
                resultDiv.style.display = 'none';
                return;
            }
            
            if (maxLength > 0 && validCount > maxLength) {
                isValid = false;
                errorDiv.textContent = `The field "${fieldName}" cannot have more than ${maxLength} item${maxLength > 1 ? 's' : ''}`;
                errorDiv.style.display = 'block';
                resultDiv.style.display = 'none';
                return;
            }
            
            if (isRequired && validCount === 0) {
                isValid = false;
                errorDiv.textContent = `The field "${fieldName}" requires at least one valid value`;
                errorDiv.style.display = 'block';
                resultDiv.style.display = 'none';
            }
        });
        
        if (!isValid) {
            return;
        }
        
        resultDiv.style.display = 'none';
        errorDiv.style.display = 'none';
        
        const fileSize = getFileSize();
        let loadingMsg = fileSize > 0 ? `Uploading ${formatBytes(fileSize)}...` : 'Uploading...';
        
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
                const listValues = [];
                
                wrappers.forEach(wrapper => {
                    const item = wrapper.querySelector('.list-item');
                    const input = item.querySelector('input, select');
                    
                    if (!input.disabled) {
                        let value;
                        
                        if (fieldType === 'checkbox') {
                            value = input.checked;
                            listValues.push(value);
                        } else if (fieldType === 'number') {
                            const numVal = input.value && input.value.trim() !== '' ? parseFloat(input.value) : null;
                            if (numVal !== null) {
                                listValues.push(numVal);
                            }
                        } else if (fieldType === 'date' || fieldType === 'time') {
                            value = input.value && input.value.trim() !== '' ? input.value : null;
                            if (value !== null) {
                                listValues.push(value);
                            }
                        } else {
                            value = input.value && input.value.trim() !== '' ? input.value : null;
                            if (value !== null) {
                                listValues.push(value);
                            }
                        }
                    }
                });
                
                formData.set(fieldName, JSON.stringify(listValues));
            });
            
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = (e.loaded / e.total) * 100;
                    updateProgress(percent);
                    if (fileSize > 0) {
                        loadingTitle.textContent = `Uploading ${formatBytes(e.loaded)} of ${formatBytes(e.total)}`;
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
                        errorDiv.textContent = 'Error: ' + data.error;
                        errorDiv.style.display = 'block';
                    }
                } catch (parseError) {
                    errorDiv.textContent = 'Error: Invalid server response';
                    errorDiv.style.display = 'block';
                }
            });
            
            xhr.addEventListener('error', () => {
                setLoading(false);
                errorDiv.textContent = 'Error: Network error';
                errorDiv.style.display = 'block';
            });
            
            xhr.addEventListener('abort', () => {
                setLoading(false);
                errorDiv.textContent = 'Upload cancelled';
                errorDiv.style.display = 'block';
            });
            
            xhr.addEventListener('timeout', () => {
                setLoading(false);
                errorDiv.textContent = 'Error: Request timeout';
                errorDiv.style.display = 'block';
            });
            
            xhr.open('POST', submitUrl);
            xhr.send(formData);
            
        } catch (err) {
            setLoading(false);
            errorDiv.textContent = 'Error: ' + err.message;
            errorDiv.style.display = 'block';
        }
    });
}

function displayResult(data) {
    resultDiv.innerHTML = '';
    
    if (data.result_type === 'image') {
        resultDiv.innerHTML = `<img src="${data.result}" alt="Result">`;
    } else if (data.result_type === 'download') {
        resultDiv.innerHTML = `
            <div class="file-download">
                <span class="file-name">📄 ${data.filename}</span>
                <button onclick="downloadFile('${data.file_id}', '${data.filename}')">Download</button>
            </div>
        `;
    } else if (data.result_type === 'downloads') {
        let html = '<div class="files-download"><h3>Files ready:</h3>';
        data.files.forEach(file => {
            html += `
                <div class="file-download">
                    <span class="file-name">📄 ${file.filename}</span>
                    <button onclick="downloadFile('${file.file_id}', '${file.filename}')">Download</button>
                </div>
            `;
        });
        html += '</div>';
        resultDiv.innerHTML = html;
    } else {
        resultDiv.innerHTML = `<pre>${JSON.stringify(data.result, null, 2)}</pre>`;
    }
    
    resultDiv.style.display = 'block';
}