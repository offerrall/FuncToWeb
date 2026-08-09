# Prefill and hidden parameters

A prefill is a set of **temporary initial values for one specific opening**: it
does not change the function, its schema, its plan or its base page.

It has two entry points: `page_of()` from Python and the `prefill` query
parameter of `GET /{slug}/`; the second builds on the first. Two more travel
alongside it, and all three describe **one opening**, never the function.

```text
prefill  → proposes initial values
hidden   → decides which parameters are not shown
autorun  → asks the page to submit itself once it is ready
```

They are independent: `hidden` does not need `prefill` and vice versa. A
function can also open another function in the space with its own return value
as the prefill, without building the URL by hand: [`OpenForm`](open-form.md)
uses this channel.

## HTTP API

```text
GET /{slug}/?prefill=<JSON object>&hidden=<JSON list of names>&autorun=1
```

The root JSON of the prefill must be an object. Its keys are parameter
names and its values travel in the browser transport format
[http.md](http.md#the-input) describes, the same one `/invoke` uses.

```javascript
const url = new URL("/tools/edit_user/", location.origin);

url.searchParams.set("prefill", JSON.stringify({name: "Ana", age: 32}));

iframe.src = url;
```

The two entry points end at the same place, `page_of()`, and the walk from the
query parameter down to it is one path written twice →
[design/prefill.md](design/prefill.md).

Any error gets a `400` **before** the page is served, never a half-filled
form:

| Query | Response |
| --- | --- |
| `prefill={not json` | `400 prefill must be valid JSON` |
| `prefill=[1, 2]` | `400 prefill must be a JSON object` |
| `prefill={"nope": 1}` | `400 unknown prefill field: 'nope'` |
| `prefill={"task_id": "two"}` | `400 task_id: expected int, got str` |
| `prefill={"title": "ab"}` | `400 title: too short: 2 chars, minimum 3` |
| `prefill={"priority": "URGENT"}` | `400 priority: expected Priority, got str` |
| `prefill={"due": "30/07/2026"}` | `400 due: expected date, got str` |
| `hidden=[not json` | `400 hidden must be valid JSON` |
| `hidden={"a":1}` | `400 hidden must be a JSON array` |
| `hidden=["a",1]` | `400 hidden must contain only strings` |
| `hidden=["nope"]` | 200: an unknown name hides nothing |
| `hidden=["a","a"]` | 200: it is hidden once |
| `hidden=[]` | 200: the same as not sending it |

From Python the same failures arrive as exceptions, with the `default:` prefix
that reveals how the prefill is applied:

```text
ValueError: unknown prefill field: 'nope'
SchemaTypeError:  age: default: expected int, got str
SchemaValueError: age: default: too large: 999, maximum 120
```

## What is base and what is temporary

`WebFunction.schema`, `WebFunction.plan` and `WebFunction.html` are compiled
once when the `WebFunction` is created and never change.

Without prefill or hidden, that base HTML is returned directly. With either of
them, and only for that opening, a temporary `Signature` is created, the
values are applied as temporary defaults, `plan_of()` validates them and
generates a plan for that opening alone, and that plan is rendered. Nothing is
stored anywhere: two openings with different prefills share no state.

## Partial prefill

A prefill does not have to cover every parameter. Parameters that do not appear
keep their original state: a required parameter stays required, a declared
default stays in place, and label, description and constraints do not change. A
required parameter included in the prefill gets a temporary default for that
opening.

## File prefill

A file field can be prefilled too, and it follows the same path as any other
value, with one extra step at each end: the reference is resolved against the
storage before the core certifies it, and it is the reference again —never the
resolved path— that is written into the plan.

```text
reference → file_resolver → real path → the core certifies
                                      → the reference is the temporary default
                                      → the widget shows it as the current
                                         file, with no pending upload
```

The local path certifies and is dropped there: it never reaches the browser,
not in the URL, not in the body and not in the message of a rejection, which
names the file and not where it is kept.

Like the rest of the prefill, it fails **before** the page is served:

| Query | Response |
| --- | --- |
| `prefill={"document": "report-<uuid>.pdf"}` | 200, with the file in place |
| `prefill={"document": "nope.pdf"}` | `400 File not found: nope.pdf` |
| `prefill={"document": "../evil.pdf"}` | `400 invalid file reference '../evil.pdf': is not a file of the storage directory` |
| `prefill={"document": "/etc/passwd"}` | `400 invalid file reference '/etc/passwd': is not a file of the storage directory` |
| `prefill={"document": "notas.txt"}` | `400 document: not an accepted file type: 'notas.txt', expected one of ('.pdf',)` |

From Python the same rule applies to the value itself, and there the failure is
an exception, since `page_of()` takes a real path and there is no resolver to
turn one into a reference:

```text
ValueError: document: default: file is not in the storage directory: 'x.pdf'
```

It works at any depth (`list[File]`, dataclasses with a file, lists of
dataclasses), because `decode()` is what walks the structure.

A prefilled file is not uploaded again: it travels in the body of `/invoke`
like any other value and the resolver recognizes it. See [files.md](files.md).

## Hidden parameters

`hidden` takes the widget out of the page. What happens to the parameter is
exactly this:

* it stays compiled into the form, with its value (the prefill's, or its own
  default);
* `form.read()` still includes it, so it **travels in the body** of `/invoke`
  and `/invoke-stream` like any other parameter;
* it still takes part in validation: hiding a parameter that has no value
  available makes the submission fail with the usual message, naming a field
  that is not visible.

The channel only checks the shape: valid JSON, a list at the root, and every
element exactly a `str`. Duplicates, ordering and unknown names are not its
business, because hiding is a visual matter and a misspelled name does not
break any contract.

### It hides, it does not lock

```text
GET /task/?prefill={"task_id":7}&hidden=["task_id"]
→ the form does not show task_id
POST /task/invoke {"task_id": 9, ...}
→ it runs with 9
```

`hidden` is not access control: the value travels in the body and a direct
call can send a different one. Authentication and permissions belong to the
host application. See [security.md](security.md).

## A CRUD on a single function

The host application builds the links:

```python
def link_of(identifier: int, task: Task) -> str:
    prefill = {
        "task_id": identifier,
        "title": task.title,
        "due": task.due.isoformat(),
        "priority": task.priority.name,
        "done": task.done,
    }

    return "/task/?" + urlencode({"prefill": json.dumps(prefill)})
```

A link with no query opens the create form; each link with a prefill edits one
record. An iframe needs no channel of its own: it opens that same URL.

## Limits

The prefill travels in the URL, with everything that implies (history,
`Referer`, access log), and there is no other channel. A prefill proposes, it
does not impose. The full list is in [limitations.md](limitations.md).

## Running the opening on its own

`autorun` asks the page to press its own submit button as soon as it is
mounted. It is the third parameter of an opening and behaves like the other
two: it belongs to that opening, it changes nothing about the function, and it
travels either from Python or in the query.

```text
GET /{slug}/?autorun=1
```

```javascript
openModal(`${SPACE}/monthly_report`, {autorun: true});
```

It exists for a modal you open to **see the answer**, not to fill in a form: a
report, a chart, a generated file, a link. Those functions often take no
parameters, or take them all prefilled by the host, so the form has nothing to
ask and the button is a step with no decision in it. Calling `/invoke` from
your own code would skip the button too, but then you get JSON and have to
draw the table, the image or the download yourself — which is exactly the work
FuncToWeb has already done.

What it does is *press the button*, and nothing else. The click that follows is
the ordinary one: the same validation, the same uploads, the same stream, the
same result card, the same [announcements to the host](sdk.md). Every rule
about a run is the rule it was already.

```text
form ready       → it runs, once
form incomplete  → nothing happens
```

An incomplete form is left **untouched**: no errors shown, no fields marked,
nothing in red. Someone who has just opened a modal has not typed anything yet
and has nothing to fix; the missing field is on screen, and their click is what
the page was waiting for anyway. From that point on the page is an ordinary
one, and clicking submit runs it.

Two things it is not:

* **Not a loop.** It presses once, at mount. A result that opens another form
  with [`OpenForm`](open-form.md) does not carry `autorun` into it unless the
  href says so.
* **Not a permission.** Whoever can open the page can already run the function
  by clicking; this only saves the click. What a page is allowed to run is
  decided by where the space is mounted and who reaches it →
  [security.md](security.md).

## Python API: `page_of()`

```python
page_of(
    web_function: WebFunction,
    *,
    prefill: Mapping[str, Any] | None = None,
    hidden: Iterable[str] | None = None,
    autorun: bool = False,
    theme: Theme = "system",
) -> str
```

```python
from func_to_web import WebFunction, page_of


web_function = WebFunction(edit_user)

html = page_of(web_function, prefill={"name": "Ana", "age": 32})
```

Returns the complete HTML of one opening. It is meant for integrations that are
more hands-on than `app_of()`: your own builders, custom HTML responses or
any flow that generates the page on its own.

* `web_function` must be a `WebFunction`; a bare function, a `WebFunctions` or
  `None` all raise `TypeError: web_function must be WebFunction`.
* `prefill` carries real Python values (`date`, `time`, `Enum` members,
  dataclasses, lists), not their JSON transport form.
* `hidden` holds parameter names. A bare `str` is rejected, because it would
  iterate character by character:
  `TypeError: hidden must be an iterable of str, not a single str`.
* `autorun` asks the page to submit itself once mounted; anything other than a
  `bool` raises `TypeError: autorun must be bool`. See
  [Running the opening on its own](#running-the-opening-on-its-own).
* `theme` is the one from [`app_of()`](router.md#theme), with the same three
  values.
* With no prefill, no hidden, no autorun and `theme="system"` it returns
  `WebFunction.html` unchanged.

The HTML expects the space assets at `../static/...`, so it needs an application
that serves them. `page_of()` creates no routes and no application: that is the
job of [`app_of()`](router.md) and [`run()`](run.md).

Related: [open-form.md](open-form.md), [sdk.md](sdk.md#embedding-a-function-page),
[web-function.md](web-function.md), [types.md](types.md).
