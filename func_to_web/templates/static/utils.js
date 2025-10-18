// ============================================================================
// UTILS.JS - Pure Functions
// ============================================================================

// ===== FORMAT & DISPLAY =====

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatUploadMessage(fileSize) {
    return fileSize > 0 ? `Uploading ${formatBytes(fileSize)}...` : 'Uploading...';
}

function formatProgressMessage(loaded, total) {
    return `Uploading ${formatBytes(loaded)} of ${formatBytes(total)}`;
}

function formatProgressPercent(loaded, total) {
    return Math.round((loaded / total) * 100);
}

// ===== PARSING =====

function parseListDefaults(defaultValue) {
    if (!defaultValue || defaultValue === 'null' || defaultValue === '[]') {
        return [];
    }
    try {
        const parsed = JSON.parse(defaultValue);
        return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
        return [];
    }
}

function parseIntOrDefault(value, defaultValue) {
    const parsed = parseInt(value);
    return isNaN(parsed) ? defaultValue : parsed;
}

// ===== VALIDATION CHECKS =====

function isValidColor(value) {
    return /^#[0-9a-fA-F]{6}$/.test(value) || /^#[0-9a-fA-F]{3}$/.test(value);
}

function isValidEmail(value) {
    return value.includes('@');
}

function isEmpty(value) {
    return !value || value.trim() === '';
}

function isListItemName(name) {
    return name.includes('[') && name.includes(']');
}

// ===== COLOR CONVERSIONS =====

function expandShortHex(color) {
    if (color.length === 4) {
        return '#' + color[1] + color[1] + color[2] + color[2] + color[3] + color[3];
    }
    return color;
}

function normalizeColorValue(value) {
    if (!value || isEmpty(value)) return '#000000';
    if (isValidColor(value)) return expandShortHex(value);
    return '#000000';
}

// ===== LIST CALCULATIONS =====

function calculateItemsToCreate(defaults, minLength) {
    if (defaults.length > 0) {
        return Math.max(0, minLength - defaults.length);
    }
    return Math.max(minLength, 1);
}

function canRemoveListItem(currentCount, minLength, isRequired, isDisabled) {
    if (isDisabled) return false;
    if (minLength > 0 && currentCount <= minLength) return false;
    if (isRequired && currentCount <= 1) return false;
    return currentCount > 1 || (!isRequired || isDisabled);
}

function canAddMoreItems(currentCount, maxLength) {
    if (!maxLength || maxLength === 0) return true;
    return currentCount < maxLength;
}

function shouldShowAddButton(index, totalCount, maxLength) {
    return index === totalCount - 1 && canAddMoreItems(totalCount, maxLength);
}

function shouldShowRemoveButton(totalCount, minLength, isRequired, isDisabled) {
    if (isDisabled) return false;
    const atMinLength = minLength > 0 && totalCount <= minLength;
    const atRequiredMin = isRequired && !isDisabled && totalCount === 1;
    return !atMinLength && !atRequiredMin && totalCount > 0;
}

// ===== FIELD VALUE EXTRACTION =====

function getFieldValue(input, fieldType) {
    if (fieldType === 'checkbox') {
        return input.checked;
    }
    if (fieldType === 'number') {
        const numVal = !isEmpty(input.value) ? parseFloat(input.value) : null;
        return numVal;
    }
    if (fieldType === 'date' || fieldType === 'time') {
        return !isEmpty(input.value) ? input.value : null;
    }
    return !isEmpty(input.value) ? input.value : null;
}

function extractListValues(wrappers, fieldType) {
    const values = [];
    wrappers.forEach(wrapper => {
        const input = wrapper.querySelector('.list-item input, .list-item select');
        if (!input.disabled) {
            const value = getFieldValue(input, fieldType);
            if (value !== null) {
                values.push(value);
            }
        }
    });
    return values;
}

function countValidListItems(wrappers, fieldType) {
    let count = 0;
    wrappers.forEach(wrapper => {
        const input = wrapper.querySelector('.list-item input, .list-item select');
        if (fieldType === 'checkbox') {
            count++;
        } else if (!isEmpty(input.value)) {
            count++;
        }
    });
    return count;
}

// ===== VALIDATION MESSAGES =====

function getValidationMessage(validity, input) {
    if (validity.valueMissing) {
        return 'This field is required';
    }
    if (validity.rangeUnderflow) {
        return `Minimum value is ${input.min}`;
    }
    if (validity.rangeOverflow) {
        return `Maximum value is ${input.max}`;
    }
    if (validity.tooShort) {
        return `Minimum length is ${input.minLength} characters`;
    }
    if (validity.tooLong) {
        return `Maximum length is ${input.maxLength} characters`;
    }
    if (validity.stepMismatch) {
        return 'Value must be a valid number';
    }
    if (validity.typeMismatch) {
        if (input.type === 'email') return 'Please enter a valid email';
        if (input.type === 'url') return 'Please enter a valid URL';
        return 'Invalid format';
    }
    if (validity.patternMismatch) {
        if (input.dataset.colorInput !== undefined) {
            return 'Please enter a valid color (#RGB or #RRGGBB)';
        }
        if (input.type === 'file') {
            return 'Please select a valid file type';
        }
        return 'Invalid format';
    }
    return 'Invalid value';
}

function getListValidationMessage(fieldName, validCount, minLength, maxLength) {
    if (minLength > 0 && validCount < minLength) {
        return `The field "${fieldName}" requires at least ${minLength} item${minLength > 1 ? 's' : ''}`;
    }
    if (maxLength > 0 && validCount > maxLength) {
        return `The field "${fieldName}" cannot have more than ${maxLength} item${maxLength > 1 ? 's' : ''}`;
    }
    return `The field "${fieldName}" requires at least one valid value`;
}

// ===== FIELD NAME GENERATION =====

function generateListItemName(fieldName, index) {
    return `${fieldName}[${index}]`;
}

function generateErrorId(inputName) {
    return `error-${inputName}`;
}

// ===== TOAST NOTIFICATIONS =====

function showToast(message, duration = 2000) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function copyToClipboard(text) {
    let cleanText = text;
    if (cleanText.startsWith('"') && cleanText.endsWith('"')) {
        cleanText = cleanText.slice(1, -1);
    }
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(cleanText)
            .then(() => showToast('✓ Copied to clipboard!'))
            .catch(() => showToast('⚠ Failed to copy', 1500));
    } else {
        const textarea = document.createElement('textarea');
        textarea.value = cleanText;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            showToast('✓ Copied to clipboard!');
        } catch (err) {
            showToast('⚠ Failed to copy', 1500);
        }
        document.body.removeChild(textarea);
    }
}