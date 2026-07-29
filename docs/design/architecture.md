# Architecture: what counts as public contract

Why the line between the public API and the visible internals falls where it
does. What is public, and what is only visible, is in
[architecture.md](../architecture.md).

## The reason is not the prefix

Below `WebFunction.return_parser` and `WebFunctions.forms` lies the resolution
machinery itself, in nodes whose names do start with `_`, and none of it,
visible or private, is needed in order to declare a function, mount it or call
it, which is what the contract undertakes to cover. A `ReturnParser` is not even
built from outside (its `root` compiles the `Download` marks into those private
nodes), so promising it stable would mean promising the shape of its machinery.
