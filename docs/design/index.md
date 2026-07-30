# Design notes

The reasoning behind the decisions the usage documentation states as contract.
Each page here answers *why*; the page it points back to answers *what*.

These notes are for whoever contributes to FuncToWeb, or is simply curious about
why something is the way it is. Nothing here is needed in order to use the
library.

* [architecture.md](architecture.md) — why the line between the public API and
  the merely visible internals falls where it does. →
  [architecture.md](../architecture.md)
* [files.md](files.md) — why `/upload` does not apply the field limit, why a
  second upload of the same reference is a `409`, and where custody of a
  promoted file ends up. → [files.md](../files.md)
* [frontend.md](frontend.md) — why the content type is decided rather than
  guessed, why every icon is a file, and why the page adds almost no color of
  its own. → [static-assets.md](../static-assets.md)
* [history-1.6-to-2.0.md](history-1.6-to-2.0.md) — why 2.0 breaks what it
  breaks: the two layers underneath were rewritten, and what that widened, lost
  and left as a limit. → [migration-1.6-to-2.0.md](../migration-1.6-to-2.0.md)
* [outputs.md](outputs.md) — why table rows are read with `itertuples()`, why a
  matplotlib figure is closed, and why a union cannot mix a download with an
  ordinary branch. → [outputs.md](../outputs.md)
* [prefill.md](prefill.md) — what happens between the `prefill` query parameter
  and the HTML that is served. → [prefill.md](../prefill.md)
* [router.md](router.md) — why both storage TTLs default to one hour, and why
  the theme is resolved in pure CSS with no selector yet. →
  [router.md](../router.md)
* [run.md](run.md) — why the space index navigates with `location.replace()`
  and carries no form logic of its own. → [run.md](../run.md)
* [sdk.md](sdk.md) — why the modal does not close itself by default, why `error`
  is not about validation, and why the payload of `result` is the envelope of
  `/invoke` again. → [sdk.md](../sdk.md)
* [streaming.md](streaming.md) — how `print()` capture works, why it is
  experimental, and why the transport polls. → [streaming.md](../streaming.md)
* [web-function.md](web-function.md) — why the description is passed through
  `cleandoc()`, and why only the first letter of a displayed name is uppercased.
  → [web-function.md](../web-function.md)

New entries go in this same flat list, one bullet per design document, in
alphabetical order by file name: the file name as the link text, an em dash, one
sentence saying what the page explains, and an arrow back to the usage page the
reasoning came from. No sections and no grouping, so a page can be appended
without restructuring anything.
