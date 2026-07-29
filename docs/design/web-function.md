# `WebFunction` metadata

Why the metadata is normalized the way it is, and why the name shown on the page
is not the name that is stored. What each field holds is in
[web-function.md](../web-function.md).

## Why the description is passed through `cleandoc()`

It is normalized for portability: in Python 3.11 and 3.12 a multi-line docstring
arrives with the indentation of the surrounding code, while 3.13 already removes
it at compile time.

## Why only the first letter

Only the **first** letter is uppercased, so an acronym or a CamelCase word keeps
its shape. This happens no matter where the name comes from: it makes no
difference whether it was derived from `fn.__name__` or written by hand in
`name=`. A name that is already written for display does not change, because it
has no `_` and its first letter is already uppercase.

The same touch-up is applied in all three places the name is displayed — the
page's `<title>` and `<h1>`, and the link in the space index — so the index link
and the page it opens never name the same function in two ways.
