// Global variables
let form, resultDiv, errorDiv, submitBtn, loadingOverlay, loadingTitle, progressBar, progressText;

// Initialize the form
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
    setupValidation();
    setupOptionalToggles();
    setupFormSubmit(submitUrl);
}

// Show/hide loading overlay
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

// Update progress bar
function updateProgress(percent) {
    progressBar.style.width = percent + '%';
    progressText.textContent = Math.round(percent) + '%';
}

// Detect file size for custom messages
function getFileSize() {
    const fileInput = form.querySelector('input[type="file"]');
    if (fileInput && fileInput.files.length > 0) {
        return fileInput.files[0].size;
    }
    return 0;
}

// Format bytes to human readable
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Setup optional field toggles
function setupOptionalToggles() {
    document.querySelectorAll('[data-optional-toggle]').forEach(toggle => {
        const fieldName = toggle.dataset.optionalToggle;
        const field = document.getElementById(fieldName);
        const colorPicker = document.querySelector(`[data-color-picker="${fieldName}"]`);
        const colorPreview = document.querySelector(`[data-color-preview="${fieldName}"]`);
        
        // Function to enable/disable field
        function updateFieldState() {
            const isEnabled = toggle.checked;
            
            if (field) {
                field.disabled = !isEnabled;
                
                if (!isEnabled) {
                    // Disabled: remove required and clear errors
                    field.removeAttribute('required');
                    const errorEl = document.getElementById(`error-${field.name}`);
                    if (errorEl) {
                        errorEl.style.display = 'none';
                    }
                    field.classList.remove('was-validated');
                } else {
                    // Enabled: ALWAYS set required and validate
                    field.setAttribute('required', 'required');
                    setTimeout(() => validateField(field), 50);
                }
            }
            
            // Handle color picker
            if (colorPicker) {
                colorPicker.disabled = !isEnabled;
            }
            
            // Handle color preview
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
        
        // Set initial state
        updateFieldState();
        
        // Listen to toggle changes
        toggle.addEventListener('change', updateFieldState);
    });
}

// Setup color input handlers
function setupColorInputs() {
    document.querySelectorAll('[data-color-input]').forEach(input => {
        const preview = document.querySelector(`[data-color-preview="${input.name}"]`);
        const picker = document.querySelector(`[data-color-picker="${input.name}"]`);
        
        input.addEventListener('input', (e) => {
            const value = e.target.value;
            if (/^#[0-9a-fA-F]{6}$/.test(value) || /^#[0-9a-fA-F]{3}$/.test(value)) {
                preview.style.backgroundColor = value;
                picker.value = value.length === 4 ? '#' + value[1] + value[1] + value[2] + value[2] + value[3] + value[3] : value;
            }
        });
        
        preview.addEventListener('click', () => {
            if (!preview.classList.contains('disabled')) {
                picker.click();
            }
        });
        
        picker.addEventListener('input', (e) => {
            input.value = e.target.value;
            preview.style.backgroundColor = e.target.value;
            if (input.classList.contains('was-validated')) {
                validateField(input);
            }
        });
    });
}

// Setup validation handlers
function setupValidation() {
    form.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('blur', () => validateField(input));
        input.addEventListener('input', () => {
            if (input.classList.contains('was-validated')) {
                validateField(input);
            }
        });
    });
}

// Validate individual field
function validateField(input) {
    const errorEl = document.getElementById(`error-${input.name}`);
    if (!errorEl) return true;
    
    // Skip validation if field is disabled
    if (input.disabled) {
        errorEl.style.display = 'none';
        return true;
    }
    
    input.classList.add('was-validated');
    
    const value = input.value || '';
    const isEmpty = value.trim() === '';
    
    // Check required
    if (input.hasAttribute('required') && isEmpty) {
        errorEl.textContent = 'This field is required';
        errorEl.style.display = 'block';
        return false;
    }
    
    // If not empty, check other constraints
    if (!isEmpty) {
        // Check minlength
        if (input.minLength && value.length < input.minLength) {
            errorEl.textContent = `Minimum length is ${input.minLength} characters`;
            errorEl.style.display = 'block';
            return false;
        }
        
        // Check maxlength
        if (input.maxLength && input.maxLength > 0 && value.length > input.maxLength) {
            errorEl.textContent = `Maximum length is ${input.maxLength} characters`;
            errorEl.style.display = 'block';
            return false;
        }
        
        // Check pattern
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
        
        // Check email type
        if (input.type === 'email' && !value.includes('@')) {
            errorEl.textContent = 'Please enter a valid email';
            errorEl.style.display = 'block';
            return false;
        }
        
        // Check number constraints
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
    
    // Fallback to browser validation
    if (!input.validity.valid) {
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
            if (input.type === 'email') {
                errorEl.textContent = 'Please enter a valid email';
            } else if (input.type === 'url') {
                errorEl.textContent = 'Please enter a valid URL';
            } else {
                errorEl.textContent = 'Invalid format';
            }
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
    } else {
        errorEl.style.display = 'none';
        return true;
    }
}

// Setup form submit handler
function setupFormSubmit(submitUrl) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        let isValid = true;
        // Only validate enabled fields
        form.querySelectorAll('input:not([type="checkbox"]):not(.color-picker-hidden):not(:disabled), select:not(:disabled)').forEach(input => {
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
        
        resultDiv.style.display = 'none';
        errorDiv.style.display = 'none';
        
        // Get file size and customize message
        const fileSize = getFileSize();
        let loadingMsg = 'Uploading...';
        if (fileSize > 0) {
            loadingMsg = `Uploading ${formatBytes(fileSize)}...`;
        }
        
        setLoading(true, loadingMsg);
        
        try {
            const formData = new FormData(form);
            
            // Use XMLHttpRequest for progress tracking
            const xhr = new XMLHttpRequest();
            
            // Upload progress tracking
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = (e.loaded / e.total) * 100;
                    updateProgress(percent);
                    
                    if (fileSize > 0) {
                        loadingTitle.textContent = `Uploading ${formatBytes(e.loaded)} of ${formatBytes(e.total)}`;
                    }
                }
            });
            
            // When upload starts
            xhr.addEventListener('loadstart', () => {
                setLoading(true, loadingMsg);
            });
            
            // When server is processing (after upload)
            xhr.addEventListener('readystatechange', () => {
                if (xhr.readyState === 3) { // LOADING
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
                        if (data.result_type === 'image') {
                            resultDiv.innerHTML = '<img src="' + data.result + '" alt="Result">';
                        } else {
                            resultDiv.innerHTML = '<pre>' + JSON.stringify(data.result, null, 2) + '</pre>';
                        }
                        resultDiv.style.display = 'block';
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