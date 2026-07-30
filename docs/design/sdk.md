# The iframe channel: three decisions

Why `closeOnResult` defaults to off, why `error` is not about validation, and
why the payload of `result` is the envelope of `/invoke` again. The contract —
the four kinds, their payloads, the rule about `v` — is in
[sdk.md](../sdk.md#the-protocol).

## `closeOnResult` is off by default

The obvious default is the wrong one. A modal that closes when the run finishes
reads well for *create task*, whose result is one line of confirmation, and
destroys the feature for everything else: an image, a table, a download link and
a printed log are all drawn **inside** the page, and closing the overlay throws
away exactly what the user opened it to see. There is no way for the library to
tell the two cases apart — the outputs arrive after the modal is already open,
and the decision has to be made before it.

So the default is the one that loses nothing: the modal stays, the host is told,
and whoever knows their function returns a confirmation asks for the autoclose.
It also keeps the release additive: a modal built before this existed behaves
after it exactly as it did, because `closeOnResult: false` *is* the old
behaviour.

## `error` means a run failed, not a field

The page has two very different kinds of bad news. A field the browser rejects
as you type —a `Min`, a `Pattern`, a required value still empty— never reaches
the server, and a field the *server* rejects arrives as a `422`. It would be
easy to send both as `error`, and the result would be a host that cannot act on
either: a message that may mean "your data is wrong, keep typing" or may mean
"the call failed" is a message you can only log.

The line drawn is the envelope's: `error` is emitted from the `error` of a
`/invoke` answer and from nowhere else, so it always means *a run happened and
did not produce outputs*. Client-side validation is silent, and so is a
malformed envelope or a request that never arrived — the page shows those where
they belong, in its own error block. This is the same separation the HTTP layer
already makes between a contract violation and an exception
([http.md](../http.md#the-status-code)): one kind, one meaning, and a host that
can branch on it.

`navigate` exists for the same reason. The [OpenForm](../open-form.md) branch
ends with the iframe moving to another form, which is neither a result nor a
failure; folding it into `result` would make `completed` true for a run that
produced nothing, and the host would refresh a list that did not change.

## The payload is the envelope again

`result` carries the same array the page has just finished drawing with — the
`result` of the `/invoke` envelope, normalized to a list, untouched. Not a
summary, not a flattened value, not a new shape.

The reason is that a second shape is a second thing to keep true. The outputs
format is already published ([outputs.md](../outputs.md)), already what `call()`
resolves to, and already what the page renders; a host that has `call()` working
can move to a modal without learning anything new, and a new output type reaches
the channel the day it reaches the renderer, with nothing to update here. A
purpose-built payload would have been shorter to read and would have started
drifting the first time an output type gained a field.

The same argument settles `results` in `closed`: it is the outputs of the **last**
run, because each `result` replaces the previous one. A list of every run would
be a new shape with no reader — a host that wants each run as it happens already
has `onResult`.

Related: [sdk.md](../sdk.md), [outputs.md](../outputs.md),
[open-form.md](../open-form.md), [security.md](../security.md).
