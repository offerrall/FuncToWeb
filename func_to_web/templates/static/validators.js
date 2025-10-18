// ============================================================================
// VALIDATORS.JS - Validation Logic (Pure validation functions)
// ============================================================================

function validateRequired(value, isRequired, isListItem) {
    const valueIsEmpty = isEmpty(value);
    
    if (isListItem) {
        if (valueIsEmpty && !isRequired) {
            return { valid: true };
        }
        if (valueIsEmpty && isRequired) {
            return { valid: false, error: 'This field is required' };
        }
    } else {
        if (isRequired && valueIsEmpty) {
            return { valid: false, error: 'This field is required' };
        }
    }
    
    return { valid: true };
}

function validateMinLength(value, minLength) {
    if (!isEmpty(value) && minLength && value.length < minLength) {
        return { valid: false, error: `Minimum length is ${minLength} characters` };
    }
    return { valid: true };
}

function validateMaxLength(value, maxLength) {
    if (!isEmpty(value) && maxLength && maxLength > 0 && value.length > maxLength) {
        return { valid: false, error: `Maximum length is ${maxLength} characters` };
    }
    return { valid: true };
}

function validatePattern(value, pattern, input) {
    if (!isEmpty(value) && pattern && !new RegExp(pattern).test(value)) {
        if (input.dataset.colorInput !== undefined) {
            return { valid: false, error: 'Please enter a valid color (#RGB or #RRGGBB)' };
        }
        if (input.type === 'email') {
            return { valid: false, error: 'Please enter a valid email' };
        }
        if (input.type === 'file') {
            return { valid: false, error: 'Please select a valid file type' };
        }
        return { valid: false, error: 'Invalid format' };
    }
    return { valid: true };
}

function validateEmailField(value) {
    if (!isEmpty(value) && !isValidEmail(value)) {
        return { valid: false, error: 'Please enter a valid email' };
    }
    return { valid: true };
}

function validateNumberField(value, min, max) {
    if (isEmpty(value)) {
        return { valid: true };
    }
    
    const numValue = parseFloat(value);
    
    if (isNaN(numValue)) {
        return { valid: false, error: 'Please enter a valid number' };
    }
    
    if (min !== '' && numValue < parseFloat(min)) {
        return { valid: false, error: `Minimum value is ${min}` };
    }
    
    if (max !== '' && numValue > parseFloat(max)) {
        return { valid: false, error: `Maximum value is ${max}` };
    }
    
    return { valid: true };
}

function validateColorField(value, isRequired) {
    const valueIsEmpty = isEmpty(value);
    
    if (valueIsEmpty && isRequired) {
        return { valid: false, error: 'This field is required' };
    }
    
    if (!valueIsEmpty && !isValidColor(value)) {
        return { valid: false, error: 'Please enter a valid color (#RGB or #RRGGBB)' };
    }
    
    return { valid: true };
}

function validateHTMLValidity(input, value) {
    if (!isEmpty(value) && !input.validity.valid) {
        const error = getValidationMessage(input.validity, input);
        return { valid: false, error };
    }
    return { valid: true };
}

function validateFieldValue(input, value) {
    const isRequired = input.hasAttribute('required');
    const isListItem = isListItemName(input.name);
    const valueIsEmpty = isEmpty(value);
    
    let result = validateRequired(value, isRequired, isListItem);
    if (!result.valid) return result;
    
    if (valueIsEmpty) {
        return { valid: true };
    }
    
    result = validateMinLength(value, input.minLength);
    if (!result.valid) return result;
    
    result = validateMaxLength(value, input.maxLength);
    if (!result.valid) return result;
    
    result = validatePattern(value, input.pattern, input);
    if (!result.valid) return result;
    
    if (input.type === 'email') {
        result = validateEmailField(value);
        if (!result.valid) return result;
    }
    
    if (input.type === 'number') {
        result = validateNumberField(value, input.min, input.max);
        if (!result.valid) return result;
    }
    
    result = validateHTMLValidity(input, value);
    if (!result.valid) return result;
    
    return { valid: true };
}

function validateListContainer(container, fieldName, fieldType) {
    const isRequired = container.dataset.listRequired === 'true';
    const isDisabled = container.dataset.disabled === 'true';
    
    if (isDisabled) {
        return { valid: true };
    }
    
    const minLength = parseIntOrDefault(container.dataset.listContainerMin, 0);
    const maxLength = parseIntOrDefault(container.dataset.listContainerMax, 0);
    const wrappers = container.querySelectorAll('.list-item-wrapper');
    const validCount = countValidListItems(wrappers, fieldType);
    
    if (minLength > 0 && validCount < minLength) {
        const error = getListValidationMessage(fieldName, validCount, minLength, 0);
        return { valid: false, error };
    }
    
    if (maxLength > 0 && validCount > maxLength) {
        const error = getListValidationMessage(fieldName, validCount, 0, maxLength);
        return { valid: false, error };
    }
    
    if (isRequired && validCount === 0) {
        const error = getListValidationMessage(fieldName, validCount, 0, 0);
        return { valid: false, error };
    }
    
    return { valid: true };
}

function showValidationError(errorEl, result) {
    if (result.valid) {
        errorEl.style.display = 'none';
        errorEl.textContent = '';
    } else {
        errorEl.textContent = result.error;
        errorEl.style.display = 'block';
    }
}

function hideValidationError(errorEl) {
    if (errorEl) {
        errorEl.style.display = 'none';
        errorEl.textContent = '';
    }
}