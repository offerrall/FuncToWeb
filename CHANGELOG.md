# Changelog

## [0.4.1] - 2025-10-10

### Added
- **Comprehensive Test Suite**: Added 96 unit tests for the `analyze()` function
  - Tests for all basic types (int, float, str, bool, date, time)
  - Tests for type annotations with Field constraints (ge, le, gt, lt, min_length, max_length)
  - Tests for special types (Color, Email, ImageFile, DataFile, TextFile, DocumentFile)
  - Tests for static and dynamic Literal dropdowns
  - Tests for optional parameters (Type | None) with and without defaults
  - Tests for error cases (unsupported types, invalid defaults, type mismatches)
  - Tests for complex functions combining multiple features
  - Full coverage of analyze() functionality

### Fixed
- **Default Value Type Validation**: Added type checking for default values in `analyze()`
  - Default values must match their parameter type (e.g., `int = "string"` now raises TypeError)
  - Validation skips optional parameters and Literal types (which have their own validation)
  - Prevents runtime errors from type mismatches between defaults and parameter types
  - Error message: `"'{param}': default value type mismatch"`

### Changed
- **Code Refactoring**: Improved code organization and maintainability
  - Extracted `analyze()` function and `ParamInfo` dataclass to separate module `analyze_function.py`
  - Cleaner separation of concerns between analysis logic and web interface
  - Easier to test and maintain individual components
  - `__init__.py` now focuses on web interface functionality
- **Testing Infrastructure**: Set up pytest-based testing framework
  - Organized tests in `tests/` directory
  - Tests run with: `pytest tests/test_analyze.py -v`

## [0.4.0] - 2025-10-09

### Added
- **Optional Parameters**: Full support for `Type | None` syntax for optional function parameters
  - Visual toggle switch to enable/disable optional fields in the UI
  - Fields with default values start enabled, fields without defaults start disabled
  - Disabled optional fields automatically send `None` to the function
  - "optional" badge indicator next to field labels for clarity
  - Works with all field types: text, number, select, date, time, color, and file inputs
  - Compatible with `Annotated` types: `Annotated[int, Field(ge=1)] | None`

### Fixed
- **Dynamic Literals String Handling**: Fixed bug where dynamic Literal functions returning single strings were incorrectly split into individual characters
  - Example: `Literal[random_mode]` where `random_mode()` returns `"Hello"` now correctly creates `('Hello',)` instead of `('H', 'e', 'l', 'l', 'o')`
  - Added proper type checking in `analyze()`, `build_form_fields()`, and `validate_params()` to handle single values vs lists/tuples
  - Dynamic functions can now return either a single value or a list/tuple of values
- **Dynamic Literal Validation**: Skip strict validation for dynamic Literal fields during form submission
  - Static literals (`Literal["A", "B"]`) validate against fixed options for security
  - Dynamic literals (`Literal[function]`) skip validation since options may change between form render and submit
  - Prevents false validation errors when dynamic options change during user interaction
  - Maintains type conversion (int/float/str) while allowing dynamic option flexibility

### Changed
- **Code Refactoring**: Improved frontend architecture with separation of concerns
  - Extracted all inline CSS from `form.html` to centralized `styles.css`
  - Separated all JavaScript logic from `form.html` into standalone `form.js`
  - Consolidated loading overlay styles into main stylesheet
  - Improved code maintainability and reusability
  - Better browser caching for static assets
  - Cleaner HTML templates with minimal inline code

### Technical Details
- **Optional Parameters Implementation**:
  - `ParamInfo` dataclass extended with `is_optional: bool` field
  - `analyze()` detects Union types with `None` using `types.UnionType` and `typing.Union`
  - Handles nested cases: `Annotated[int | None, Field(...)]` and `int | None`
  - `build_form_fields()` adds `is_optional` and `optional_enabled` flags to field specs
  - `validate_params()` checks for `{field}_optional_toggle` in form data to determine if field is enabled
  - Frontend JavaScript `setupOptionalToggles()` manages enable/disable state and required attributes
- **Frontend Structure**:
  - `form.html`: Clean template with only Jinja2 templating logic, includes optional field toggle switches
  - `form.js`: Modular JavaScript with `initializeForm()` and `setupOptionalToggles()` functions
  - `styles.css`: Complete styling including optional field toggle switches, disabled states, and badges
- **Dynamic Literals Fix**: Added `isinstance(result_value, (list, tuple))` check before converting to tuple to prevent string decomposition
- **Union Type Detection**: Compatible with both Python 3.10+ (`int | None`) and Python 3.9 (`Union[int, None]`) syntax
- Benefits: Easier debugging, better separation of concerns, improved performance through caching, enhanced flexibility for optional parameters

## [0.3.0] - 2025-10-08

### Added
- **Upload Progress Tracking**: Real-time progress bar and file size display during uploads
  - Visual spinner and overlay while uploading/processing
  - Dynamic progress percentage (0-100%)
  - File size display in human-readable format (KB, MB, GB)
  - Status messages: "Uploading X of Y", "Processing..."
  - Disabled submit button during upload to prevent duplicate submissions

### Fixed
- **Debug Mode Compatibility**: Fixed uvicorn.run() crash when running in debug mode
  - Replaced direct `uvicorn.run()` call with manual server setup using `uvicorn.Config` and `uvicorn.Server`
  - Resolves `loop_factory` parameter conflict with asyncio debugger patching
  - Server now starts correctly in both normal and debug modes
(Thanks to @vmatt for reporting and solving this issue)

### Changed
- **Optimized File Upload Performance**: Implemented streaming for large file uploads
  - Replaced full-file memory loading with chunked streaming (8MB chunks)
  - Reduced memory footprint for large files (1GB+ uploads)
  - Added configurable `CHUNK_SIZE` and `FILE_BUFFER_SIZE` constants
  - New `save_uploaded_file()` async function for optimized file handling
  - Enhanced uvicorn configuration with increased limits:
    - `limit_concurrency=100` for more simultaneous connections
    - `limit_max_requests=1000` for longer-running workers
    - `timeout_keep_alive=30` for persistent connections
    - `h11_max_incomplete_event_size=16MB` for larger upload buffer
  - Performance improvement: ~237 MB/s for 1GB files on localhost on normal SSD
- Replaced `fetch()` with `XMLHttpRequest` in frontend for upload progress tracking
- Refactored server initialization to use explicit uvicorn configuration object
- Improved compatibility with Python debugging tools and IDEs

## [0.2.0] - 2025-10-07

### Added
- **Dynamic Dropdowns**: Support for functions inside `Literal` type hints to generate dropdown options dynamically at runtime
- New example `15_dynamic_dropdowns.py` demonstrating dynamic dropdown usage
- Documentation section for dynamic dropdowns in README.md

### Changed
- Enhanced `analyze()` function to detect and execute callable objects in `Literal` types
- Improved dropdown flexibility for API-driven or context-dependent options

## [0.1.0] - 2025-10-05

### Added
- Initial release
- Support for basic types (int, float, str, bool, date, time)
- Special input types (Color, Email)
- File uploads (ImageFile, DataFile, TextFile, DocumentFile)
- Static dropdowns with Literal
- Validation with Pydantic Field constraints
- Image and plot return types (PIL, matplotlib)
- Multi-function server support
- 14 comprehensive examples
