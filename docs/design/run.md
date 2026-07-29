# The space index

Why the page `run()` adds at `/` is as thin as it is. What it draws, and the
markup it draws it with, is in [run.md](../run.md#the-space-index).

## Why the index navigates with `location.replace()`

On load and on every `hashchange`, the link whose `data-slug` matches is looked
up. The chosen function opens in an `<iframe>` that navigates with
`location.replace()`, so the selection does not fill up the history, and
re-selecting the page already on screen does not reload it.

## Why it carries no form logic

The index **does not duplicate the form or its logic**: it carries no plan, no
fields, no widget system, only links and an iframe to the pages that already
exist, and that is why it cannot fall out of sync with them. It only navigates
same-origin pages; pointing it at a foreign origin is outside the contract.
