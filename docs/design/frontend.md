# Frontend: assets, icons and color

Why the served assets, the icons and the palette are what they are. The
contract — the routes, the content types, the theme attribute and the caching —
is in [static-assets.md](../static-assets.md).

## Why the content type is decided, not guessed

Guessing would give different results from machine to machine: on Windows
`mimetypes` reads the registry, where `.js` is often `text/plain`, and a module
served that way does not run. The three extensions in
[the table](../static-assets.md#a-tree-not-a-list) are the ones the two
libraries ship, so the table is the whole answer.

## Why every icon is a file

All SVGs are files, in both layers: no inline SVG, no `data:` URIs, no base64,
no geometry built in the browser, no icon fonts, and no remote assets.
FuncToWeb's icons are drawn with `mask-image` from `page.css`, so they keep
`currentColor` and follow the theme like any other text. The URL is relative to
the style sheet, so they work under any `prefix`.

## Not one extra color

Almost all the color comes from the `widgets.css` palette, including the color
of the [space index](../run.md#the-space-index): its `<body>` is also a
`.pth-root`, and its sidebar shares `--pth-surface` with the page it frames,
separated only by the border. The index and the form are visible at the same
time, and a hand-mixed gray next to a palette calibrated on `#12151b` reads as
two different products.

Two exceptions remain, both `--ftw-*` and declared in the five blocks at the top
of `page.css`: the `:root` with the values, and the four theme blocks (system
light, system dark, forced `light`, and forced `dark`) that choose between them:

```text
--ftw-success-color     the ✓ mark on an output; the palette has no green
--ftw-scrollbar-thumb   the scrollbar hangs off <html>, outside any
                        .pth-root, so there are no tokens to read there
```

The second one repeats the value of `--pth-input-border` by hand, rather than a
gray of its own: it is a palette color placed where the token does not reach.

`--ftw-color-scheme` is declared in those same blocks, and it is not a color:
it carries `light` or `dark` to the `color-scheme` of `<html>`, so that native
controls and the scrollbar follow the theme.
