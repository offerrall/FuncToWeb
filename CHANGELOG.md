# Changelog

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