# URL Prefill

Every function has its own URL. Pass query parameters to open the form with fields pre-filled:

```
http://127.0.0.1:8000/my-function?name=Alice&age=30
```

Parameter names must match the function's parameter names exactly. Values are coerced to the correct type automatically.

## Use Cases

**Link directly to a pre-configured form:**
```
http://127.0.0.1:8000/send-report?format=pdf&recipient=admin@company.com
```

**Embed in an existing web app via iframe:**
```html
<iframe src="http://127.0.0.1:8000/process-image?radius=5"></iframe>
```

**Open from a script:**
```python
import webbrowser
webbrowser.open("http://127.0.0.1:8000/analyze?threshold=0.8&mode=strict")
```

## How It Works

Prefill works for all scalar types (`str`, `int`, `float`, `bool`, `date`, `time`). File inputs cannot be prefilled via URL. Optional fields are enabled automatically when a value is provided.

This is the same mechanism `ActionTable` uses internally — clicking a row navigates to the destination function's URL with the row data as query params.
