# Changelog

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