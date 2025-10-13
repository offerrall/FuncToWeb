# func-to-web Feature Backlog

> **Note:** These are potential features that may or may not be implemented. Just an ideas list.

---

## Quick Wins

### Field Descriptions / Tooltips
- [ ] Extract `description` from Field in `analyze()`
- [ ] Add `<span class="tooltip">` in HTML template
- [ ] CSS for tooltip hover effect
- [ ] Write tests for description parsing
- [ ] Update documentation

### Clear Form Button
- [ ] Add clear button next to Submit in `form.html`
- [ ] Implement `clearForm()` function in `form.js`
- [ ] Style button to match existing design
- [ ] Reset to default values (not empty)
- [ ] Add keyboard shortcut (Ctrl+K)

### Copy Result to Clipboard
- [ ] Add "Copy" button in `#result` div
- [ ] Implement `copyResult()` using `navigator.clipboard`
- [ ] Create toast notification "Copied!"
- [ ] CSS for toast animation
- [ ] Handle copy errors gracefully

---

## Medium Effort

### Form Sections / Groups
- [ ] Add `sections` parameter to `run()`
- [ ] Auto-detect sections by field name prefixes
- [ ] Generate HTML with `<fieldset>` and `<legend>`
- [ ] CSS for collapsible sections
- [ ] Update form.js to handle section state
- [ ] Write tests for section grouping
- [ ] Add example to examples/ folder
- [ ] Update README

### Improved Loading States
- [ ] Parse docstring from function
- [ ] Display docstring during processing
- [ ] Add estimated time if available
- [ ] Show spinner animation variations
- [ ] Update loading overlay HTML/CSS

---

## Bigger Features

### Fullscreen Mode for Results
- [ ] Modal overlay component
- [ ] Click on image/plot to expand
- [ ] Keyboard navigation (Esc to close)
- [ ] Zoom controls for images
- [ ] CSS animations for open/close
- [ ] Mobile-friendly gestures

### Keyboard Shortcuts
- [ ] Ctrl+Enter → Submit form
- [ ] Ctrl+K → Clear form
- [ ] Esc → Close modals/fullscreen
- [ ] Show shortcuts help (Ctrl+?)
- [ ] Add shortcuts overlay UI
- [ ] Update documentation

### Auto-save Form State
- [ ] Save form values on change to localStorage
- [ ] Restore on page reload
- [ ] Add "Resume last session" prompt
- [ ] Clear auto-save after successful submit
- [ ] Handle multiple functions

### Field Dependencies
- [ ] Syntax for conditional fields
- [ ] Show/hide fields based on other values
- [ ] Enable/disable based on conditions
- [ ] Update validation for dependencies
- [ ] Write comprehensive tests
- [ ] Update documentation with examples

### Custom Field Types
- [ ] Documentation for creating plugins
- [ ] Tests for plugin system

---

## Nice to Have

- [ ] Favicon support via `run(favicon="🚀")`
- [ ] Custom CSS via `run(custom_css="path/to/style.css")`
- [ ] Auto-focus first field on load
- [ ] Better error messages with hints
- [ ] Retry button on upload failure
- [ ] Drag and drop for file uploads

---

## Out of Scope

- Authentication/authorization (use reverse proxy)
- Database integration (keep it simple)
- Multi-step forms/wizards (separate functions)
- Real-time collaboration (maybe in future)
- Built-in deployment tools (use Docker/Railway)
- GraphQL support (REST is enough)
- Websockets for long-running tasks (polling works)