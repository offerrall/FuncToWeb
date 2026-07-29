# Static assets

`GET /static/{path}` serves the assets that every function in a space shares. It
is a router route, like [`/doc`](api-docs.md), not a per-function route: there is
one per space, and every page in that space pulls from it, so they share the
download and the cache. That is why `static` is a reserved slug.

## Two sources, in order

1. `func_to_web/static`, FuncToWeb's own assets;
2. `pytypehintweb.STATIC`, the widget layer's assets.

The first one that exists is served, so if the same name existed in both,
FuncToWeb would win.

FuncToWeb's own assets are five files and one folder:

| Asset | What it is |
| --- | --- |
| `page.js` | Builds a function page from the plan embedded in the markup, and runs it |
| `upload.js` | The upload that precedes `/invoke`, with its progress modal |
| `output.js` | The rendering of the outputs with their copy and download buttons |
| `page.css` | The style of that page |
| [`sdk.js`](sdk.md) | The helpers a frontend of your own calls the space with |
| `icons/` | The five SVGs the outputs use |

`sdk.js` is the one no function page asks for: it is served because it is an
asset like any other, not because the page graph reaches it.

Everything else comes from `pytypehintweb` (`form.js`, `widgets.css`, its own
`icons/`, and the modules they import), served from wherever the package is
installed, with nothing copied or repackaged.

## A tree, not a list

`{path}` can contain subdirectories, because the style sheets reference their
icons relatively:

```text
/{prefix}/static/widgets.css        →  url("./icons/trash.svg")
/{prefix}/static/icons/trash.svg
```

What decides what gets served is resolution, not pattern matching: the path is
resolved, and it must still land inside one of the two directories and must be a
file. A traversal (`../router.py` and its encoded variants), an absolute path, a
symlink pointing outside, or a directory all get a `404`, with no distinction
between "not there" and "not allowed".

The content type is decided here, not guessed:

```text
.js    text/javascript
.css   text/css
.svg   image/svg+xml
```

Those are the three extensions the two libraries ship. Why the type is decided
here rather than guessed is a deliberate choice →
[design/frontend.md](design/frontend.md#why-the-content-type-is-decided-not-guessed).

## Icons

All SVGs are files, in both layers, and FuncToWeb's own are drawn with
`mask-image` from `page.css`, so they keep `currentColor` and follow the theme
like any other text. The URL is relative to the style sheet, so they work under
any `prefix`. What that rules out, and why →
[design/frontend.md](design/frontend.md#why-every-icon-is-a-file).

## No absolute paths on a function page

Icons are not a special case. **Everything** a function page requests, it
requests relatively: `../static`, `../upload`, `../returns/…`, `./icons/*.svg`.
That way the router prefix is inherited from the page's own URL, and nothing the
page loads has to know where the space was mounted. See [router.md](router.md).

The [index that `run()` adds](run.md#the-space-index) is the exception: its three
prefixed references — the style sheet, `/doc`, and the `src` of each iframe —
are built by prepending the prefix rather than relatively. That is not a problem
because `run()` always mounts at the root and passes the index an empty prefix;
the index is not part of the router, so it does not go with the router to
another mount.

## Theme

`page.css` carries no widget palette: it relies on the `--pth-*` tokens from
`widgets.css`, which exist only inside a `.pth-root`. That is why **the
`<body>` of every page is that root**, and the whole page (header, button,
outputs, and upload modal) reads the same tokens by inheritance and paints a
single surface.

The server writes `data-pth-theme` on the `<html>` element from the `theme` of
[`router_of()`](router.md#theme), as part of the initial markup, and
`widgets.css` resolves the three values in pure CSS: there is nothing to run in
`<head>` and no preference to restore
([design/router.md](design/router.md#why-the-theme-is-pure-css)).

Almost all the color comes from the `widgets.css` palette. Two `--ftw-*`
exceptions remain, plus `--ftw-color-scheme`, which is not a color: why there
are exactly those and not one more is a rule worth reading →
[design/frontend.md](design/frontend.md#not-one-extra-color).

## Caching

Responses carry `Cache-Control: public, max-age=3600` and an `ETag` computed
from the file. A request with a matching `If-None-Match` gets a `304` with no
body, repeating `ETag` and `Cache-Control`; one that does not match gets the
full file again.

That is what makes the browser download the widgets once per space instead of
once per function, even while the index keeps swapping the iframe.

Related: [router.md](router.md), [run.md](run.md),
[sdk.md](sdk.md#embedding-a-function-page).
