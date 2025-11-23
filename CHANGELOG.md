# Changelog

## [0.8.0] - 2025-11-23

### Added
- **Back Button Navigation**: Added back button on form pages to return to tools index

### Changed
- **Dark/Light Theme Toggle**: Complete redesign with SVG icons
  - Replaced emoji icons with SVG moon/sun icons for better alignment and aesthetics

- **Field Label Formatting**: Labels now automatically replace underscores with spaces
  - `user_name` displays as "User Name"
  - `api_url` displays as "Api Url"

- **Function Description Styling**: Improved appearance of function docstrings

### Fixed
- **Button Alignment**: Fixed vertical misalignment between theme toggle and back button
  - Resolved CSS inheritance issue where global `button` selector was adding `margin-top: 0.5rem`

- **Number Input Controls (Dark Mode)**: Fixed visibility of increment/decrement arrows in dark mode
  - Applied `color-scheme: dark` for native dark mode styling
  - Arrows now properly visible against dark backgrounds

- **Simplified optional field interface**: 
  - Removed `optional` badge labels from field names for cleaner design
  - Removed "Enable field" text label next to toggle switches
  - Toggle switches now self-explanatory without redundant text
  - Cleaner, more minimal form appearance

### Improved
- **CSS Architecture**: Enhanced maintainability and reduced inheritance issues
  - Removed redundant CSS properties
  - Cleaner separation between component styles
- **Example Code**: Better examples in /examples folder with improved comments
- **Update examples images**: Regenerated example images

## [0.7.6] - 2025-11-14

### Fixed
- **PyPI README**: Fixed missing README.md display on PyPI package page
  - Added `long_description` and `long_description_content_type` to package metadata

## [0.7.5] - 2025-11-14

### Fixed
- **Long text output handling**: Fixed layout overflow when functions return long strings (e.g., 100+ character passwords)
  - Added word-wrapping and proper text overflow handling in result containers
  - Applied `word-break: break-all` and `overflow-wrap: break-word` to prevent layout breaking
  - Improved responsive behavior for long outputs on mobile devices

## [0.7.4] - 2025-10-26

### Added
- **Function Descriptions**: Functions with docstrings now display their description below the title in the web UI
  - Extracted using `inspect.getdoc()` for clean formatting
  - Centered text with improved contrast in dark mode
  - Styled with left border accent matching the theme

### Changed
- **Code Refactoring**: Reduced code duplication in `run.py`
  - Created `create_response_with_files()` helper function for file download responses
  - Created `handle_form_submission()` async function to consolidate form processing logic
  - Eliminated duplicate code between single and multiple function modes
  - Improved maintainability and consistency across endpoints

## [0.7.3] - 2025-10-25

### Changed
- **Complete Documentation Rewrite**: Restructured entire documentation using MkDocs Material for better navigation and user experience
  - Organized into clear categories: Input Types, Types Constraints, Output Types, and Other Features
  - Added dedicated pages for each feature with visual examples and code snippets
  - Improved progressive learning flow with "Next Steps" navigation
  - Enhanced README with direct links to all major documentation sections
  - Better mobile responsiveness and dark mode support

## [0.7.2] - 2025-10-18

### Added
- **Auto-focus First Field**: Cursor automatically focuses on the first input field when the page loads, improving keyboard navigation
- **Keyboard Shortcuts**: 
  - `Ctrl+Enter` (or `Cmd+Enter` on Mac) to submit the form from any input field
  - Works only when submit button is not disabled
- **Copy to Clipboard**: JSON results now include a "Copy" button to copy output to clipboard
- **Toast Notifications**: Elegant toast messages for user feedback (e.g., "✓ Copied to clipboard!")
  - Auto-dismisses after 2 seconds
  - Adapts to light/dark themes using CSS variables
  - Fallback for older browsers without Clipboard API

### Changed
- **Frontend Refactoring**: Complete restructuring of JavaScript codebase for improved maintainability and code organization
  - Extracted pure utility functions to `utils.js`
  - Separated DOM construction logic to `builders.js`
  - Isolated validation logic to `validators.js`
  - Added DOM manipulation helpers in `main.js` for cleaner state management
  - Reduced cognitive load with single-responsibility functions
  - Improved code reusability and testability

## [0.7.1] - 2025-10-17

### Fixed
- **Optional List Fields**: Hide add (+) and remove (-) buttons when optional list fields are disabled
- **Error Messages on Disabled Fields**: Clear error messages when fields are disabled
- **Initial State Consistency**: Fixed inconsistent behavior between page load and toggle interactions
- **Minimum List Items**: Lists with minimum item requirements now auto-create all required items

## [0.7.0] - 2025-10-13

### Added
- **Dark Mode**: Toggle between light and dark themes with persistent preference
  - Floating theme toggle button (🌙/☀️) in top-right corner
  - Theme preference saved in localStorage
  - Smooth transitions between themes
  - Optimized color scheme for dark mode with proper contrast
  - Works on both form and index pages
  - Animated toggle button with hover effects
  - Mobile-responsive button sizing

## [0.7.0] - 2025-10-13

### Added
- **Dark Mode**: Toggle between light and dark themes with persistent preference
  - Floating theme toggle button (🌙/☀️) in top-right corner
  - Theme preference saved in localStorage
  - Smooth transitions between themes
  - Optimized color scheme for dark mode with proper contrast
  - Works on both form and index pages
  - Animated toggle button with hover effects
  - Mobile-responsive button sizing

## [0.6.0] - 2025-10-13

### Added
- **File Download Support**: Return files from functions with automatic download buttons
  - Return single file: `FileResponse(data=bytes, filename="file.txt")`
  - Return multiple files: `[FileResponse(...), FileResponse(...)]`
  - **Streaming downloads**: Efficient handling of large files (GB+) without memory issues
  - Works with any file type: PDF, Excel, ZIP, images, binary data, etc.
  - No size limits: Uses temporary files and streaming like file uploads
  - Clean UI: File list with individual download buttons
  - Automatic cleanup: Temp files deleted after download
  - Example:
```python
    def create_report(name: str):
        pdf_bytes = generate_pdf(name)
        return FileResponse(data=pdf_bytes, filename="report.pdf")
```

## [0.5.0] - 2025-10-12

### Added
- **List Support**: Full support for list parameters with dynamic add/remove items
  - Syntax: `list[int]`, `list[str]`, `list[float]`, `list[Color]`, `list[ImageFile]`, etc.
  - Works with all basic types: `int`, `float`, `str`, `bool`, `date`, `time`
  - Works with special types: `Color`, `Email`, `ImageFile`, `DataFile`, etc.
  - Item-level constraints: `list[Annotated[int, Field(ge=1, le=100)]]`
  - List-level constraints: `Annotated[list[int], Field(min_length=2, max_length=10)]`
  - Combined constraints: `Annotated[list[Annotated[int, Field(ge=0)]], Field(min_length=2)]`
  - Dynamic UI: Add/remove buttons to manage list items
  - Optional lists: `list[str] | None` or `list[str] | OptionalDisabled`
  - Default values: `list[str] = ["hello", "world"]`
  - **Default behavior**: Lists without explicit values default to `None` (not `[]`)
    - `list[int]` → `default = None`
    - `list[int] = []` → `default = None` (empty lists converted to `None`)
    - `list[int] = [1, 2]` → `default = [1, 2]` (only non-empty lists preserved)
  - Item-level validation: Each list item validates against type constraints
  - List-level validation: Validates `min_length` and `max_length` constraints
  - Visual feedback: Individual error messages per list item
  - Empty/whitespace values automatically filtered out

## [0.4.5] - 2025-10-12

### Fixed
- **Color Picker UI Bug**: Fixed color picker not opening when clicking on color preview box
  - Removed CSS properties that prevented programmatic clicks (`pointer-events: none`, extreme positioning)
  - Simplified hidden color input positioning using `width: 0`, `height: 0`, and `z-index: -1`
  - Maintained visual appearance while ensuring browser can open native color picker
  - Color picker now properly opens on preview click for both regular and optional fields

## [0.4.4] - 2025-10-11

### Added
- **Explicit Optional Control**: New `OptionalEnabled` and `OptionalDisabled` markers for precise control over optional field initial state
  - `Type | OptionalEnabled`: Field always starts enabled, regardless of default value
  - `Type | OptionalDisabled`: Field always starts disabled, even with default value
  - Explicit markers override automatic behavior (presence of default value)
  - Works with all types: basic types, special types (Color, Email), constraints, and Literals
  - Backwards compatible: standard `Type | None` syntax continues working with automatic behavior
- **Test Suite for Optional Markers**: 44 tests covering explicit optional control
  - All basic types with both markers (int, str, float, bool, date, time)
  - Special types (Color, Email) with markers
  - Constraints combined with markers
  - Default value override behavior
  - Mixed usage (automatic + explicit in same function)
  - Edge cases (markers with `= None`)
  - **316 total tests** across all modules (130 + 88 + 88)

### Changed
- **ParamInfo dataclass**: Added `optional_enabled` field to store initial toggle state
- **analyze()**: Enhanced Union type detection to identify OptionalEnabled/OptionalDisabled markers
- **types.py**: Added marker classes and type aliases for explicit optional control

## [0.4.3] - 2025-10-10

### Added
- **Test Suite for build_form_fields()**: 88 tests covering HTML field generation, constraint extraction, and edge cases
  - All field types: text, number, checkbox, select, date, time, color, email, file
  - Format conversions: date → ISO, time → HH:MM
  - Constraint handling: min/max/step for numbers, minlength/maxlength for strings
  - Dynamic Literal re-execution and error cases (empty lists, mixed types)
  - Edge cases: Unicode (😀🚀), negative/large values (1e100), leap years, boundary constraints
  - Complex scenarios: 9+ parameter functions, mixed optional states, order preservation
  - All tests pass in 0.58s

### Changed
- **Code Refactoring**: Extracted `build_form_fields()` to dedicated module
  - New module: `build_form_fields.py` with pattern constants
  - New module: `process_result.py` for result handling
  - New module for custom patterns: `custom_pydantic_types.py`
  - Three core modules: `analyze_function.py`, `validate_params.py`, `build_form_fields.py`
  - **272 total tests** across all modules (96 + 88 + 88)

## [0.4.2] - 2025-10-10

### Added
- **Test Suite for validate_params()**: 88 tests covering type conversion, validation, and edge cases
  - Type conversions: strings → int/float/bool/date/time
  - Constraint validation: numeric bounds, string length, pattern matching
  - Optional toggle behavior, checkbox handling, hex color expansion (#abc → #aabbcc)
  - Edge cases: negative numbers, scientific notation (1.5e10), Unicode (Héllo 世界 🌍), leap years
  - All tests pass in 0.53s

### Changed
- **Code Refactoring**: Extracted `validate_params()` to dedicated module
  - New module: `validate_params.py`
  - **184 total tests** (96 + 88)

## [0.4.1] - 2025-10-10

### Added
- **Test Suite for analyze()**: 96 tests covering function signature analysis
  - All types, constraints, special types (Color, Email, Files), Literals, optionals
  - Error cases: unsupported types, invalid defaults, type mismatches

### Fixed
- **Default Value Type Validation**: Added type checking for defaults in `analyze()`

### Changed
- **Code Refactoring**: Extracted `analyze()` and `ParamInfo` to `analyze_function.py`

## [0.4.0] - 2025-10-09

### Added
- **Optional Parameters**: Full `Type | None` support with visual toggle switches
  - Fields with defaults start enabled, without defaults start disabled
  - Works with all types and constraints

### Fixed
- **Dynamic Literals**: Single string returns no longer split into characters
- **Dynamic Literal Validation**: Skip validation since options can change between render and submit

### Changed
- **Frontend Refactoring**: Separated CSS/JS from templates
  - `form.html` → clean template only
  - `form.js` → all JavaScript logic
  - `styles.css` → all styling

## [0.3.0] - 2025-10-08

### Added
- **Upload Progress**: Real-time progress bar, file size display, status messages

### Fixed
- **Debug Mode**: Fixed uvicorn crash with asyncio debugger

### Changed
- **Upload Performance**: 8MB chunk streaming, ~237 MB/s on localhost
  - Replaced `fetch()` with `XMLHttpRequest` for progress tracking

## [0.2.0] - 2025-10-07

### Added
- **Dynamic Dropdowns**: Functions in `Literal` generate options at runtime

## [0.1.0] - 2025-10-05

### Added
- Initial release with basic types, files, validation, images/plots, multi-function support
