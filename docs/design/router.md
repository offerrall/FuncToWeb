# The router

Why the storage defaults and the theme are what they are. The contract — the
signature, the errors, the routes and the one-process-one-policy rule — is in
[router.md](../router.md).

## Why both TTLs default to one hour

Both default to one hour because what the library manages on its own is meant
to be ephemeral: an upload nobody claimed and a download link nobody kept. And
they are two settings, not one, so a space can hold its uploads for a week and
still hand out downloads that live an hour.

## Why the theme is pure CSS

The attribute goes in the initial markup; JavaScript does not add it after
load, so the theme is resolved before the first paint and there is no flicker
in any of the three cases: `system` is resolved by `widgets.css` with
`prefers-color-scheme`, in pure CSS, and the other two arrive already decided.

A `WebFunction` carries no theme of its own, because it compiles its HTML once,
without knowing which router it will end up in. That is why the theme belongs
to the space and two themes need two routers.

> Today the theme is set by whoever mounts the space. Letting the user
> choose it, and remembering that choice, will come in a future version: that is
> why there is no visible selector yet, no `localStorage`, no cookies, and no
> theme-switching JavaScript.
