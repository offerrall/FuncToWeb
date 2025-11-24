# Server Configuration

Customize the server host, port, and template directory.

## Basic Usage

```python
from func_to_web import run

def my_function(x: int):
    return x * 2

# Single function
run(my_function, host="127.0.0.1", port=5000)

# Multiple functions
run([func1, func2], host="127.0.0.1", port=5000, template_dir="my_templates")
```

## Parameters

- **`func_or_list`** - Single function or list of functions to serve
- **`host`** - Server host (default: `"0.0.0.0"`)
- **`port`** - Server port (default: `8000`)
- **`template_dir`** - Custom template directory (optional)

## Common Configurations

**Localhost only:**
```python
run(my_function, host="127.0.0.1")
```

**Custom port:**
```python
run(my_function, port=5000)
```

**Network accessible (default):**
```python
run(my_function, host="0.0.0.0", port=8000)
```

**Custom templates:**
```python
run(my_function, template_dir="my_custom_templates")
```

For use custom templates, copy the default templates from the ./func_to_web/templates/ directory and modify as needed, then specify the path in `template_dir`.
With custom templates, you can change the look and functionality of the web interface.

---

## That's It!

You've completed the func-to-web documentation. Check out the [examples folder](https://github.com/offerrall/FuncToWeb/tree/main/examples) for 19 complete, runnable examples.
