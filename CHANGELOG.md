# Changelog

## [1.6.0] - 2026-06-05

## [1.6.0] - 2026-06-06

### Security 

(by https://github.com/Dr1985)
- Fixed a path traversal vulnerability in file uploads. The original
  filename from the multipart request was joined into the save path
  without sanitization, allowing `../` sequences to escape `uploads_dir`
  and write files to arbitrary locations. Filenames are now reduced to
  their final path component. Thanks to the reporter for the catch.

### Fixed
- **The package no longer ships unrelated top-level folders** — `setuptools` was
  discovering every directory that looked like a package, so `pip install
  func-to-web` dropped `_private/`, `docs/` and `examples/` into the user's
  `site-packages` as global top-level packages (visible in the old
  `top_level.txt`). Packaging is now scoped with `include = ["func_to_web*"]` in
  `[tool.setuptools.packages.find]`, so only `func_to_web` is installed.
- **Returned files are now stream-copied instead of being read fully into RAM** —
  `save_returned_file` used `Path(...).read_bytes()` + `write_bytes()` for the
  `FileResponse(path=...)` case, loading the entire file into memory just to
  rewrite it (a 2 GB return meant 2 GB of RAM), which defeated the whole point of
  passing `path=`. It now copies in 8 MB chunks via `shutil.copyfileobj`. The
  in-memory `data=` branch is unchanged.
- **Result serialization no longer blocks the event loop** — the function's
  return value was serialized (writing returned files, base64-encoding
  PIL/matplotlib PNGs, building tables) directly inside the running coroutine.
  For `async` functions this always ran on the event loop; for `sync` functions
  the `to_thread` wrapper only covered the call itself, not the serialization.
  A large output froze the server for every connected user. `process_result` now
  runs via `asyncio.to_thread`, moving all heavy CPU/IO off the loop regardless
  of whether the user's function is sync or async.
- **The per-function param list is no longer mutated concurrently** —
  `create_handlers` analyzed the function once into a single `params` list that
  was captured by the `page_handler`/`submit_handler` closures and shared across
  every request. `page_handler` rewrote it in place on each render
  (`refresh_params`), so two concurrent requests — e.g. a slow `Dropdown(func)`
  refresh racing another render, or a render racing a submit's validation — could
  serialize or validate against a half-refreshed list. The shared list is now an
  immutable template (`base_params`); each page render builds its own refreshed
  copy (`[p.refresh_choices() for p in base_params]`), and submit validation
  reads the template directly (dynamic dropdown options aren't validated
  server-side, so the submit never needed fresh choices). No shared mutable
  state, no locks — the same principle as the 1.5.0 globals cleanup, applied to
  the last place mutable shared state remained.
- **Invalid `Params` setups are now rejected at startup with a clear error
  instead of misbehaving silently** — three cases that previously slipped
  through: a field name colliding across the flat form (a `Params` field
  matching a function parameter or a field from another `Params` class)
  made `params_by_name` keep only the last one, so the form rendered
  duplicate inputs and validation/reconstruction stole values between them;
  a nested `Params` field and an optional `Params` parameter
  (`data: UserData | None`, both `typing.Union` and PEP 604) fell through
  to the generic analyzer and crashed with a cryptic internal error.
  All three now raise an explicit `ValueError` when routes are registered,
  naming the offending field/parameter and how to fix it (rename the field;
  flatten the nested class; make individual fields optional inside the
  class instead). Valid code is unaffected.
- **Server-side validation errors (HTTP 422/400) are now shown in the UI instead
  of being silently dropped** — the frontend fed every submit response through
  the SSE parser; a 422 is plain JSON, matched no SSE blocks, and was discarded
  without a trace, so submits failing server-only validation (notably a `Params`
  `__post_init__` raising `ValueError`) appeared to do nothing. Non-200 responses
  are now detected in both submit paths (fetch and XHR upload) and rendered in
  the error block, listing each offending field and its message. Client-side
  validation masked this for ordinary field constraints, which is why it went
  unnoticed until server-only validation existed.

### Changed
- **`Params` subclasses are now frozen dataclasses** — `Params` was an empty
  marker class and instances were rebuilt internally via `object.__new__` +
  attribute assignment, which silently skipped any user-defined `__init__` and
  produced half-constructed objects. Subclassing `Params` now applies
  `@dataclass(frozen=True)` automatically: instances are constructible anywhere
  (`UserData(name=..., email=...)`), comparable, hashable, and immutable, with
  `dataclasses.replace()` for variants. Cross-field validation goes in
  `__post_init__`; a `ValueError` raised there surfaces as a 422 form error.
  Breaking: defining a custom `__init__` is no longer supported (the dataclass
  generates it), and mutating a Params instance now raises `FrozenInstanceError`.
  Internally, the manual `_reconstruct` step is gone — construction is just
  `YourClass(**fields)`.

### Removed
- **`aiofiles` dependency dropped** — it was used in a single place, the chunked
  write loop in `save_uploaded_file`. The same non-blocking behavior is now
  achieved with a plain `open()` and `await asyncio.to_thread(f.write, chunk)`
  (the upload read stays `await uploaded_file.read(...)` via Starlette's
  `UploadFile`). At 8 MB chunks the thread-hop overhead is negligible. One fewer
  dependency, no behavior change.

### Documentation
- **Upload cleanup docs corrected** — `files.md` claimed FuncToWeb "skips cleanup
  on files that no longer exist in the original path", describing a mechanic that
  doesn't exist. The temporary upload folder is always removed after the function
  finishes; `shutil.move()` works because it moves the file out of that folder
  before deletion, not because of any skip.
- **`Params` cross-field validation documented** — `/doc` and `api-docs.md` now
  note that a 422 `errors` key may be a single field *or* a `Params` group whose
  `__post_init__` rejected an otherwise field-valid combination; `params.md` adds
  that this validation runs server-side (the error appears on submit, not while
  typing) and a `Limitations` section spelling out the nested / optional /
  duplicate-name cases that are rejected at startup.

## [1.5.0] - 2026-06-04

This release is a big simplification pass. The goal: remove features that can be done more elegantly other ways, and make FuncToWeb composable.

1.5.0 takes FuncToWeb from "tool for spinning up mini programs" to "a library you can use both ways": `run()` serves your functions standalone, exactly as it always has, and the new `create_app()` returns a plain FastAPI app you can mount inside your own. Nothing from the original mode is lost — the auto-generated form UI, single/multi function apps, and everything you already use keep working exactly as before.

### Added
- `create_app()`: builds the FuncToWeb FastAPI application without starting a
  server. This makes the library embeddable — mount it inside a larger app —
  and unlocks `uvicorn --workers N` / `--reload` by serving via import string
  (both are rejected by `run()`, which serves an app instance):

  ```python
  from fastapi import FastAPI
  from func_to_web import create_app

  host = FastAPI()
  host.mount("/tools", create_app([add, multiply]))
  ```

  All internal URLs are derived per request from the ASGI `root_path`, so a
  mounted app works under any prefix with no configuration. `run()` is now a
  thin wrapper: guards + startup sweeps + `create_app()` + Uvicorn.

  Note: the startup sweeps (leftover upload folders, expired returned files)
  run only in `run()`. `create_app()` deliberately skips them — under multiple
  workers, each worker builds its own app, and sweeping the shared directories
  on every build could delete a sibling worker's in-flight uploads during
  rolling restarts. Expired returned files are still cleaned opportunistically
  at runtime.

### Changed
- **Internal CSS/JS bundles are now built in memory and served from routes, not written to a temp dir** — `create_pytypeinput_assets()` (which concatenated pytypeinputweb + `internal_static` assets and wrote `styles.css`/`scripts.js` to `<temp>/func_to_web/static`, mounted at `/static`) is replaced by `build_static_assets()`, which returns the two bundles as strings; they're served by two FastAPI routes captured in a closure. Why: the temp-dir files let two processes (or two installed versions) clobber each other's bundles, and caused `PermissionError` on shared multi-user temp dirs on Linux. Nothing is written to disk anymore. The internal asset URLs changed: `/static/styles.css` → `/_functoweb/static/styles.css` and `/static/scripts.js` → `/_functoweb/static/scripts.js` (internal URLs).
- **Returned-file cleanup is now opportunistic instead of timer-based** — the per-process background daemon thread (`start_cleanup_timer`) that swept `returns_dir` every `returns_lifetime` seconds has been removed. Cleanup now runs lazily on activity — when a file is saved (`FileResponse`) or downloaded — throttled by a `.last_cleanup` marker file so it does real work at most once per `returns_lifetime` window. Why: under the upcoming multi-process `create_app()` deployments, N workers would have spawned N redundant threads sweeping the same directory (and a library spawning daemon threads is undesirable in general); the marker approach is multi-process safe by being harmless (no locks — duplicate deletes are ignored). Observable contract change: expired files are now deleted on the next save/download after expiry rather than on a fixed timer; the boot-time cleanup in `run()` still applies. `returns_lifetime` keeps the same meaning.
- **Internals are now free of module-level config state** — the upload/return directories, size limit and `stream_prints` flag are no longer mutated onto module globals (`save_file_handler.UPLOADS_DIR`, etc.); `run()` resolves them as locals and passes them down explicitly through closures. Public behaviour is unchanged, but anyone who used to monkey-patch `save_file_handler.UPLOADS_DIR` (or the other module globals) must pass the corresponding `run()` keyword instead.
- **Default uploads and returned-files directories moved to the OS temp folder** — `uploads_dir` now defaults to `<os-temp-dir>/func_to_web_uploads` and `returns_dir` to `<os-temp-dir>/func_to_web_returned_files` (resolved via `tempfile.gettempdir()`), instead of `./uploads` and `./returned_files` in the current working directory; transient files no longer pollute the project folder and the OS reclaims them automatically. Pass an explicit `uploads_dir=...` / `returns_dir=...` to keep the previous behaviour
- **`root_path` passed inside `fastapi_config` is now forwarded to FastAPI instead of being silently stripped** — the internal filtering existed to protect a build-time `root_path` that no longer exists (mounted apps get their prefix per request from Starlette; `run()` passes `root_path` through to Uvicorn). Note that setting it there is normally unnecessary and can double prefixes if combined with mounting or `run(root_path=...)`.
- **Public namespace is now declared explicitly via `__all__` in `func_to_web/types.py`** — previously `from .types import *` (no `__all__`) leaked every transitive import into the package root, so `func_to_web.json`, `func_to_web.Path`, `func_to_web.BaseModel`, `func_to_web.dataclass`, `func_to_web.Any`, `func_to_web.Callable` and `func_to_web.model_validator` all existed as accidental, undocumented re-exports. These are no longer accessible from the package root (or via `from func_to_web.types import *`); import them from their real source (`json`, `pathlib`, `pydantic`) instead. The deliberate surface is unchanged: `Field`, `Annotated`, `Literal`, `date`, `time`, `Params`, `FileResponse` and all pytypeinput types (`Color`, `Email`, `File`, `Slider`, …) remain exported, and explicit imports like `from func_to_web.types import Email` are unaffected.
- **Hardcoded Uvicorn deployment defaults removed**
- **`root_path` parameter removed from `run()`'s signature** — now passed through to Uvicorn via `**uvicorn_kwargs`, which injects it into the ASGI scope. `run(func, root_path="/tools")` works exactly as before (no trailing slash; the previous auto-normalization is gone).
- **Sidebar navigation replaced by a "back to index" button** — multi-function pages no longer render the left sidebar listing every function (and its mobile toggle/overlay). Each function page now shows only a small back button that returns to the index, which remains the single place that lists all functions. Simpler chrome, less code (the whole sidebar template, its JS and CSS are gone). Single-function apps are unchanged (no index, no button).
- **FastAPI's Swagger UI / ReDoc / OpenAPI schema are off by default** — `/docs`, `/redoc` and `/openapi.json` now return `404`. The functions are exposed by name, not as typed OpenAPI operations, so that auto-generated schema misdescribed them; `/doc` is the honest, machine-readable description. Re-enable via `fastapi_config` (e.g. `create_app(func, fastapi_config={"openapi_url": "/openapi.json", "docs_url": "/docs"})`). When mounted with `create_app()`, your host app's own docs are untouched.
- **Internal CSS/JS bundles are now browser-cacheable** — `/_functoweb/static/styles.css` and `scripts.js` are served with `Cache-Control: max-age=3600` and a content-hash `ETag`. Repeat loads within the window hit the browser cache (zero requests); after it expires the browser revalidates cheaply with `If-None-Match` and gets a `304` instead of re-downloading. A restart with new code changes the hash, so stale bundles invalidate themselves.

### Removed
- Authentication (`auth`/`secret_key`). No compatibility shims remain: passing
  them now fails with a plain `TypeError`/Uvicorn error. Protect your app with
  a reverse proxy that handles auth (e.g. Nginx basic auth).
- `front_dir` / `assets_dir` from `run()`. Superseded by composition: mount
  your static site next to the tools with Starlette's `StaticFiles`:

  ```python
  host = FastAPI()
  host.mount("/tools", create_app(funcs))
  host.mount("/", StaticFiles(directory="dist", html=True))
  ```
- **`keep_uploads` parameter** — removed from `run()`. Uploaded files were transient by design and are always cleaned up after the function finishes; persisting them is now done explicitly by moving the file out of `uploads_dir` (e.g. with `shutil.move()`) before returning
- **`ActionTable`** — removed entirely, with no backward compatibility:
  returning one now falls through to the generic `str()` text output, and the
  `action_table` SSE result type no longer exists. It coupled navigation to a
  table widget and had been marked experimental since its introduction. For
  standalone tools, functions remain directly reachable by URL with prefill;
  for CRUD apps with their own frontend, mount `create_app()` inside FastAPI
  and drive forms via URL prefill + embed mode. A first-class navigable
  output (`Link`) is planned after the API stabilizes.
- **`HiddenFunction`** — removed, with no backward compatibility: importing it
  now fails with an `ImportError`, and every registered function always appears
  in the index and navigation. The flag had no audience: with `run()` you want
  all your tools visible (the index is the UI), and when mounting via
  `create_app()` nobody looks at that index — if you need internal endpoints
  separated from visible tools, mount two apps
  (`host.mount("/tools", create_app(visible))` /
  `host.mount("/api", create_app(internal))`), which composes cleaner than a
  per-function flag.
- **Function groups** — passing a dict (or nested dicts) to `run()`/`create_app()`
  to build collapsible, slug-prefixed navigation groups is gone. `run()` now
  accepts only a single function or a flat list; every function lives at its own
  top-level `/<slug>`. To separate sets of tools, mount several `create_app()`
  apps under different FastAPI paths instead — it's clearer and removes a
  confusing nesting mechanism.

### Fixed
- **Internal URLs are now prefix-aware (work under a `root_path` / when mounted)** — the HTML/JS emitted absolute, root-anchored URLs (`/submit`, `/download/<id>`, `/_functoweb/static/...`, navigation/index links). Behind a reverse proxy with a real `root_path`, or under `app.mount("/tools", ...)`, those pointed at the domain root and broke styling, form submit, navigation and downloads. URLs are now derived per request from `request.scope["root_path"]` and prepended to internal paths (templates receive a `prefix`; the frontend reads `window.__functoweb_prefix`). The SSE payload is unchanged, as is `/doc`, the API contract and `run()`'s public signature. This also paves the way for the mountable `create_app()` added in this release.
- **`workers` and `reload` passed to `run()` are now rejected instead of silently ignored** — `run()` hands the app *instance* to Uvicorn, and Uvicorn only spawns multiple workers, or runs its reload supervisor, when given an import string (`"module:app"`). A `workers=N` (N > 1) or `reload=True` in `**uvicorn_kwargs` therefore had no effect: callers believed they had N processes / auto-reload while actually running a single, non-reloading process. `run(func, workers=2+)` and `run(func, reload=True)` now raise an explicit `ValueError`. **Migration:** `workers=1` (or omitting it) is unchanged; for real multiprocess or auto-reload, build the app with `create_app()` (added in this release) and serve it by import string with `uvicorn`/`gunicorn` (e.g. `uvicorn mymodule:app --workers 4 --reload`).

### Internal
No observable behaviour change; dead-code and vestigial cleanup.
- **Package reorganized by responsibility** — the arbitrary root-vs-`core/` split is gone. The public API (`__init__`, `run`, `types`, `models`) and shared foundations (`normalization`, `constants`, `utils`) sit at the package root; the rest moved into themed subpackages: `serving/` (server, routes, request handlers), `rendering/` (templates/builder, `/doc`), `execution/` (function call, result/table serialization, print capture) and `files/` (upload/return persistence). Public imports (`from func_to_web import ...`, `from func_to_web.types import ...`) are unchanged; only internal module paths moved.
- **`FunctionMetadata` is now the single source of truth for multi-function apps** — the parallel `navigation_data` list of `{name, slug, description, url}` dicts (built by `build_navigation_structure()` and stored on `NormalizedInput`) duplicated the `FunctionMetadata` objects already in `items`, since every URL is just `/<slug>`. It's gone: templates, the index redirect and route registration read `items` directly, slug-uniqueness is validated in `normalize_items()`, and the now-trivial helpers `build_navigation_structure()`, `register_navigation_routes()` and `detect_input_type()` were removed (the last two inlined). No behaviour change.
- **Removed a dead destructure binding in `zz-form.js`** — `getOrCreateContainer` was pulled out of `window.functoweb.result` but never used (only `clearContainer` and `renderResult` are); it stays exported by `result-renderer.js`, which uses it internally.

## [1.0.2] - 2026-05-02

### Fixed
- **`ActionTable` cell serialization for list / tuple / dict values** — non-scalar cells were being rendered with Python's `str()`, producing invalid output like `['34', 'aaa']` (single quotes, not parseable as JSON)
  - Now serialized with `json.dumps`, producing standard `["34","aaa"]`
- **`ActionTable` row click sent `None` cells as the literal string `"None"` in the URL** — clicking a row produced URLs like `?tags=None`, which the prefill layer treated as a real value (activating optional toggles, failing to JSON-parse list fields)
  - `None` is now preserved through serialization and the row-click handler omits the parameter entirely, matching the prefill contract (absent param == no value)
- **`ActionTable` row click dropped embed mode when redirecting to another function** — clicking a row in an embedded form (`?__embed=1`) navigated to the target function without the embed flag, so the destination rendered with full chrome (sidebar, theme toggle, opaque background) inside the iframe
  - The row-click handler now detects `__embed=1` on the current page and propagates it to the redirect URL, keeping the whole action chain embedded
- **Single quotes / apostrophes in `Description(...)` and `PatternMessage(...)` broke the form** — param metadata is serialized to JSON and injected into the `<pti-form params='...'>` attribute, which is delimited by single quotes; any apostrophe in the text closed the attribute early and broke the rendered form
  - The serialized JSON is now HTML-escaped in the template (`params='{{ params_json | e }}'`), so apostrophes (and `"`, `<`, `&`) survive as entities and are decoded back to the original JSON when the `<pti-form>` web component reads the attribute
### Changed
- **Default `limit_max_requests` raised from 1000 to 10000** — the previous limit recycled the Uvicorn worker too aggressively for apps serving many static assets per page (e.g. image grids), causing the process to restart mid-session
- **Fixed pytypeinput and pytypeinputweb version numbers in dependencies** — updated to the latest versions (1.0.2 and 1.0.3 respectively) to ensure compatibility with the new features and fixes in those libraries
- **Uploads and returned-files directories are now created lazily** — `uploads/` and `returned_files/` are no longer created at server startup; each directory is created on demand the first time a file is actually uploaded or returned, so apps with no file I/O never create them

## [1.0.1] - 2026-04-28

### Added
- **Custom frontend hosting via `front_dir` and `assets_dir`** — `run()` now accepts two new parameters to serve a custom frontend from the same process
  - `front_dir`: directory mounted at `/front` with `html=True` for SPA-style routing — drop a static site, landing page, or built React/Vue/Svelte bundle next to your Python functions
  - `assets_dir`: directory mounted at `/assets` for images, fonts, downloads or any static files referenced by your frontend or forms
  - Both are excluded from the auth middleware so static content is reachable without login
  - Lets a single FuncToWeb process host the form UI, the API and a full custom frontend — no separate web server needed

- **`/doc` endpoint** — auto-generated, machine-readable API documentation
  - Every app now exposes `GET /doc` returning a single plain-text document
  - Lists all registered functions (visible and hidden) with their parameters,
    constraints, choices, defaults, and a working `curl` example for each
  - Parameters are emitted as JSON, making the doc directly parseable
  - File parameters include an `upload_info` block describing the multipart
    transport, field name, and whether multiple files are accepted
  - Dynamic dropdowns (`Dropdown(func)`) are flagged with `"dynamic": true`
    so consumers know the listed options are a snapshot, not an exhaustive set
  - URLs in examples use a `<base_url>` placeholder, making the doc portable
    across local, proxied and production deployments
  - Designed to be consumed by humans, scripts, or AI agents calling the API
    without prior knowledge of the app

- **Embed mode for iframe integration** — append `?__embed=1` to any function URL
  - Strips the sidebar, theme toggle, and outer chrome at runtime
  - Forces a transparent background so the form blends into the parent page
  - Removes the container's max-width, padding, shadow and border
  - Lets you drop a FuncToWeb form into an existing web app via `<iframe>` with
    no visual seams — combine with URL prefill (`?param=value`) for a fully
    pre-configured embedded form

## [1.0.0] - 2026-04-15

Biggest release so far. The library has been rewritten from the ground up — most existing code works without changes or with very minor ones.

The biggest structural change is that FuncToWeb is now split into three independent libraries:

- **[pytypeinput](https://github.com/offerrall/pytypeinput)** — Analyzes Python type hints and extracts UI metadata. No web dependency.
- **[pytypeinputweb](https://github.com/offerrall/pytypeinputweb)** — Renders HTML forms from `pytypeinput` metadata. Use it in your own server.
- **[func-to-web](https://github.com/offerrall/functoweb)** — The full stack.

This opens up a lot of new possibilities — for example, using FuncToWeb as a support layer inside an existing web app, exposing individual utility functions without building a full tool. There are other interesting approaches worth exploring that the docs cover.

**A full re-read of the documentation is recommended.**

This is a **stable beta**. I'll be actively fixing issues and improving things over the coming days.

## [0.9.14] - 2026-04-01
### Fixed
- Starlette compatibility issue
  - Added explicit starlette<1.0.0


## [0.9.13] - 2026-01-13
### Added
- **Multiple file upload improvements for `list[FileType]`**
  - New "+" button next to file input allows adding files from different folders
  - Visual file list shows selected files with names, sizes, and remove buttons
  - Supports all file types: `ImageFile`, `VideoFile`, `AudioFile`, `DataFile`, `TextFile`, `DocumentFile`, `File`
  - Files can be selected from one folder, then more added from other folders
  - Individual files can be removed before upload
  - File list automatically hides when optional field is disabled

### Changed
- Improved UX for file uploads with real-time feedback and preview
- Only frontend changes, fully backwards compatible with existing backend logic

## [0.9.12] - 2026-01-11
### Added
- **New `Dropdown()` type for dynamic dropdowns** - cleaner, type-safe syntax for dropdowns with runtime-generated options
  - Use `Annotated[str, Dropdown(get_options)]` instead of `Literal[get_options]`
  - Provides better IDE support and clearer intent
  - Example:

```python
    from typing import Annotated
    from func_to_web.types import Dropdown
    
    def get_users():
        return ['alice', 'bob', 'charlie']
    
    def send_message(to: Annotated[str, Dropdown(get_users)]):
        return f"Message sent to {to}"
```

  - Works with `str`, `int`, `float`, and `bool` types
  - Fully backwards compatible - `Literal[func]` syntax still supported

## [0.9.11] - 2026-01-07
### Added
- Grouped functions feature: organize multiple functions into collapsible accordion groups
  - Pass a dictionary to `run()` with group names as keys and function lists as values
  - Example: `run({'Math': [add, multiply], 'Text': [upper, lower]})`
  - Groups display as accordion cards with badges showing function count
  - Only one group can be open at a time for clean navigation
  - Fully backwards compatible with existing single function and list modes

## [0.9.10] - 2026-01-01
### Added
- VideoFile and AudioFile types for file uploads
  - `VideoFile`: Accepts common video formats (mp4, mov, avi, mkv, wmv, flv, webm, mpeg, mpg)
  - `AudioFile`: Accepts common audio formats (mp3, wav, aac, flac, ogg, m4a)
- Updated ImageFile type to include additional formats (raw, psd)
- FileResponse now accepts either binary data or file path
  - `FileResponse(data=bytes, filename="file.ext")` - for in-memory files
  - `FileResponse(path="/path/to/file", filename="file.ext")` - for existing files on disk
  - Files specified by path are copied to returns_dir for consistent management
  - Both approaches result in automatic 1-hour cleanup

### Changed
- Changed default title of index page from "Function Tools" to "Menu"

## [0.9.9] - 2025-12-23

### Performance
- **Non-blocking Execution**: Standard Python functions (`def`) are now automatically executed in a thread pool. This prevents CPU-heavy tasks from blocking the main event loop.
- **Async Disk I/O**: Offloaded `FileResponse` processing and disk writing to background threads.
  - Generating and saving large files (GB+) no longer freezes the server.
  - The UI remains responsive for other users while files are being written to disk.
- **Improved Concurrency**: The server can now handle multiple simultaneous heavy requests (calculations or downloads) without queue blocking.

## [0.9.8] - 2025-12-21

### Changed
- **FileResponse Filename Limit**: 150-character maximum (Pydantic validated)

### Security
- **Filename Sanitization**: User-uploaded files sanitized against directory traversal, reserved names, and special characters
  - Format: `{sanitized_name}_{32char_uuid}.{ext}`
  - 100-char limit on user portion, ~143 total length
  - Preserves original name for identification

### Fixed
- **File Lists**: Fixed bug where `list[File]` would fail with JSON parsing error
  - Backend now uses `form_data.getlist()` to properly group uploaded files
  - `validate_list_param()` accepts pre-processed lists in addition to JSON strings


## [0.9.7] - 2025-12-10

### Philosophy Change

Version 0.9.6 introduced SQLite for file tracking, blocked multiple workers, and added complex configuration. This was overengineered. func-to-web should be simple, fast, and reliable.

0.9.7 returns to simplicity with filesystem-based tracking, multiple workers support, and sensible defaults.

---

### Removed

- **SQLite Database**
  - No more database files or locks
  - File metadata encoded directly in filenames
  - Format: `{uuid}___{timestamp}___{filename}`

- **Parameters Removed**
  - `db_location` - no longer needed
  - `cleanup_hours` - now hardcoded to 1 hour

- **Workers Limitation**
  - `workers > 1` no longer blocked
  - Scale vertically without restrictions

### Added

- **Automatic Upload Cleanup**
  - New parameter: `auto_delete_uploads` (default: `True`)
  - Uploaded files deleted after function completes
  - Disable with `auto_delete_uploads=False` if needed

- **Directory Configuration**
  - New parameter: `uploads_dir` (default: `"./uploads"`)
  - New parameter: `returns_dir` (default: `"./returned_files"`)

### Changed

- **File Retention**
  - Returned files deleted 1 hour after creation (hardcoded)
  - No download tracking needed
  - Cleanup runs every hour automatically

- **Multiple Workers**
  - Now supported like any other Uvicorn option
  - Each worker runs independent cleanup
  - File operations are atomic, no conflicts

- **Architecture**
  - Removed `db_manager.py` module
  - Simplified `file_handler.py`
  - Faster startup (no database initialization)

### Fixed

- Database lock errors eliminated
- Race conditions eliminated
- Improved startup performance

### Documentation

- Updated all docs to remove SQLite references
- Removed `db_location` and `cleanup_hours` from examples
- Added `auto_delete_uploads` documentation
- Updated API reference (removed `db_manager`)

### Migration from 0.9.6

**Before:**
```python
run(my_function, db_location="/data", cleanup_hours=48)
```

**After:**
```python
run(my_function, uploads_dir="/data/uploads", returns_dir="/data/returns")
# Files now expire after 1 hour (hardcoded)
```

**Breaking Changes:**
- `db_location` removed (use `returns_dir`)
- `cleanup_hours` removed (hardcoded to 1 hour)
- `func_to_web.db` no longer created

**Non-Breaking:**
- `workers` parameter now supported
- All other parameters unchanged

### Summary

0.9.6 was overengineered. 0.9.7 is simple again: no database, automatic cleanup, multiple workers supported. Filesystem operations are fast, atomic, and sufficient.

## [0.9.6] - 2025-12-10

### Added
- **Automatic Periodic Cleanup**: Files are now automatically cleaned up every hour while the server runs.
  - No need to restart the server for cleanup to occur
  - Cleanup task runs in background every 3600 seconds (1 hour)
  - Files older than `cleanup_hours` are removed from both disk and database
  - Configurable via `cleanup_hours` parameter (default: 24 hours)
  - Set `cleanup_hours=0` to disable periodic cleanup

- **Thread-Safe File Cleanup**: Implemented threading locks to prevent race conditions during concurrent file cleanup operations.
  - Per-file locks ensure only one thread can clean up a specific file at a time
  - Lock registry automatically cleaned up after operations complete
  - Prevents "file not found" errors when multiple threads/requests attempt cleanup simultaneously
  - Safe for high-concurrency environments with async I/O

- **Database Health Monitoring**: Added automatic monitoring for file registry size.
  - Displays warning if database contains >10,000 file references on startup
  - Helps identify when manual cleanup or configuration changes are needed
  - New `get_file_count()` function in `db_manager` module

- **Enhanced Security**: Added UUID validation for file download endpoints.
  - Validates file IDs match UUID v4 format before database queries
  - Returns 400 Bad Request for malformed file IDs
  - Additional layer of protection against injection attempts

### Changed
- **Workers Limitation**: Multiple workers (`workers > 1`) are now explicitly blocked and will raise a clear error.
  - Prevents SQLite database corruption from concurrent writes across processes
  - Displays educational error message with scaling alternatives
  - Recommends running multiple instances with Nginx instead
  - Single worker can handle 500-1,000 req/s with async I/O (sufficient for most teams)

- **Database Location Validation**: Improved validation and path handling for `db_location` parameter.
  - Automatically creates directories if path is a directory
  - Validates parent directory exists for file paths
  - Raises clear error messages with actionable guidance
  - Better support for custom database locations

- **Database Connection Timeouts**: Added 5-second timeout to SQLite connections to prevent deadlocks.

### Fixed
- **FileNotFoundError Handling**: Improved error handling when uploaded or returned files are manually deleted from disk.
  - Auto-healing: broken database references are cleaned up automatically
  - Returns "File expired" instead of internal server error
  - Graceful degradation when files are missing

- **Lock Cleanup**: Threading locks are now properly cleaned up in `finally` blocks.
  - Prevents lock registry from growing indefinitely
  - Eliminates potential memory leaks in long-running processes

### Documentation
- **File Upload Cleanup Clarification**: Updated `files.md` to clearly explain OS cleanup behavior.
  - Added comparison table for Linux/macOS/Windows automatic cleanup
  - Warning for Windows users about potential file accumulation
  - Three cleanup strategies with code examples (OS, manual, in-memory)
  - Clear distinction between uploaded files (not auto-cleaned) and returned files (auto-cleaned)

- **Scaling Guidelines**: Added comprehensive scaling section to `server-configuration.md`.
  - Explains why multiple workers aren't supported (SQLite limitations)
  - Documents single worker performance capabilities (500-1,000 req/s)
  - Provides step-by-step guide for horizontal scaling with multiple instances
  - Nginx sticky sessions configuration for load balancing
  - Enterprise alternatives for >1,000 concurrent users

- **Updated API Documentation**: All docstrings revised for consistency.
  - No inline comments (per style guide)
  - Comprehensive function/class documentation
  - Clear parameter descriptions with examples

### Refactored
- **Modular Architecture**: Complete code reorganization into specialized modules for better maintainability.
  - `server.py`: Main server configuration and entry point
  - `routes.py`: Routing setup and request handling
  - `file_handler.py`: File upload/download operations with thread-safe cleanup
  - `db_manager.py`: SQLite database operations for file tracking
  - `auth.py`: Authentication middleware and session management
  - `analyze_function.py`: Function signature analysis and metadata extraction
  - `validate_params.py`: Form data validation and type conversion
  - `build_form_fields.py`: HTML form field generation from type hints
  - `process_result.py`: Result processing for different output types
  - `check_return_is_table.py`: Table format detection and conversion
  - `types.py`: Type definitions and custom types (Color, Email, File types)
  - `__init__.py`: Clean public API with minimal exports (`run`, type helpers)
  
- **Benefits**:
  - Separation of concerns: Each module has a single, clear responsibility
  - Easier testing: Modules can be tested independently
  - Better code navigation: Find functionality quickly by module name
  - Reduced coupling: Clear interfaces between components
  - Future-proof: Easy to extend without touching unrelated code

## [0.9.5] - 2025-12-09

### Added
- **New Generic `File` Type**: Added support for a generic `File` type hint.
  - Use `from func_to_web.types import File` to accept uploaded files of **any** extension.
- **Expanded File Extensions**: Significantly broadened the list of supported formats for specific file types.

## [0.9.4] - 2025-12-08

### Added
- **Python Enum Support**: Full support for Python `Enum` types as dropdown menus.
  - Use standard Python enums as type hints: `def func(theme: Theme)`
  - Supports `str`, `int`, and `float` enum values
  - Automatic conversion from form values back to Enum members
  - Your function receives the actual Enum member (e.g., `Theme.LIGHT`), not just the string value
  - Access both `.name` and `.value` properties in your function
  - Optional enums with `Theme | None` syntax
  - Compatible with all enum features (methods, properties, iteration)
  - Add tests covering enum handling, conversion, and edge cases
  
### Benefits
- **Type Safety**: Full IDE autocomplete and type checking
- **Reusability**: Define enum once, use across multiple functions
- **Rich Semantics**: Access both enum name and value, add custom methods
- **Clean Code**: No repetition of `Literal['option1', 'option2']` in every function signature

## [0.9.3] - 2025-11-30

### Fixed
- **Async Function Support**: Fixed an issue where passing an `async def` function displayed a `<coroutine object>` instead of the result.
  - The library now automatically detects `async` functions and `awaits` them properly.
  - Enables seamless integration with async libraries (e.g., `httpx`, `tortoise-orm`, `motor`).

## [0.9.2] - 2025-11-25

### Added
- **Built-in Authentication**: Robust, stateless authentication system.
  - Enable simply by passing a dictionary `auth={"username": "password"}` to the `run()` function.
  - Architecture based on **Signed Cookies** (no database required).
  - Includes protection against **Timing Attacks** (`secrets.compare_digest`) and **CSRF** (`SameSite='Lax'`).
- **Session Management**: New `secret_key` argument in `run()` to control session persistence across server restarts.
- **Login UI**:
  - Dedicated, modern login page that automatically inherits the application's theme (Light/Dark).
  - Responsive design matching the core library aesthetics.
- **Logout Functionality**: New logout button in the header navigation (automatically appears when auth is enabled).

### Changed
- **Dependencies**: Added `itsdangerous` to required packages (essential for session signing).
- **Templates**: Updated `base` templates to handle conditional rendering based on authentication state (`has_auth` flag).

## [0.9.1] - 2025-11-24

### Added
- **Reverse Proxy Support**: New `root_path` argument in `run()` to properly handle deployments behind Nginx, Traefik, or Docker containers with path prefixes.
- **Advanced Server Configuration**: Any extra keyword arguments passed to `run()` (`**kwargs`) are now forwarded directly to **Uvicorn**.
  - Enables SSL/HTTPS support (`ssl_keyfile`, `ssl_certfile`).
  - Allows performance tuning (`workers`, `limit_max_requests`, `timeout_keep_alive`).
- **Custom API Metadata**: New `fastapi_config` dictionary argument to customize the underlying FastAPI application (e.g., changing the API title, version, or disabling swagger docs).

## [0.9.0] - 2025-11-24

### Added
- **Table Rendering**: Automatic HTML table generation from multiple data formats
  - `list[dict]` - Headers extracted from dictionary keys
  - `list[tuple]` - Auto-generated headers (Column 1, Column 2, etc.)
  - **Pandas DataFrame** - Direct support with column names as headers
  - **NumPy 2D Arrays** - Renders with auto-generated headers
  - **Polars DataFrame** - Native support with column names
  - Tables can be combined with other outputs in tuples/lists
  - Zebra striping for better readability

### Changed
- **Form Container**: Added horizontal resize capability on desktop (≥1025px)
  - Default width: 500px
  - Resizable from 400px to 1400px by dragging the edge
  - Disabled on tablets and mobile devices
  - Maintains responsive behavior with proper padding

- **Result Display**: Enhanced UI/UX for output presentation
  - Replaced text-based "Copy" button with a subtle, floating SVG icon in the top-right
  - Optimized vertical alignment to perfectly center text relative to the button
  - Removed enclosing quotes from string results (both in display and clipboard)
  - Improved button state logic to handle rapid clicks and timeouts robustly

## [0.8.1] - 2025-11-24

### Added
- **Multiple Outputs**: Functions can now return tuples or lists to display multiple outputs simultaneously
  - Combine text, images, plots, and file downloads in a single response
  - Example: `return ("Analysis complete", processed_image, plot_figure, report_file)`
  - Nested tuples/lists are not supported (validation with clear error message)
  - Each output type rendered in its own container with proper spacing

### Changed
- **Output Processing**: Enhanced `process_result()` to handle tuple/list returns recursively
- **Response Format**: Backend now supports `result_type: 'multiple'` with nested outputs array
- **Frontend Rendering**: New `createMultipleOutputs()` function in builders.js for recursive rendering

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
