# Changelog

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