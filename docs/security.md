# Security and limits

FuncToWeb publishes functions. Who may call them is decided by the application
you mount it in.

## What FuncToWeb guarantees

- **Input is validated before the function runs**, recursively, against the
  signature.
- **Files stay in their directories.** A file travels as a bare name, never as a
  path: `..`, separators, absolute paths and symbolic links pointing outside are
  refused, and a server path never reaches the browser.
- **A stored file cannot be replaced**: uploading an existing reference again is
  a `409`.
- **Output is written as text**, never as HTML.

## What is up to you

- **Authentication and permissions.** FuncToWeb has none, and `run()` protects
  nothing: put the space behind the authentication of your application.
- **Execution limits**: time, memory and concurrency.
- **Keeping or deleting used files**, which FuncToWeb keeps forever.
- **File sizes that must hold for any client**: `FileHint`'s sizes are checked
  only by the browser.
- **Error messages**: an exception's message reaches the client as it is.
- **Hidden values**: `hidden` hides a field but does not lock it, a prefill
  travels in the URL (history, logs), and an embedded page shares its results
  with whoever embeds it.

## Limits

- Tables are shown whole, without sorting, search or pages; images travel whole
  inside the response.
- A stream cannot be cancelled: the function runs to the end.
- Storage settings are one per process: two spaces with different upload
  directories need two processes.
- The theme belongs to the space, not to the user: there is no switcher.
- There is no deployment guide: workers, SSL and reloading belong to your
  server.
