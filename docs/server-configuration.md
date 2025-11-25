# Server Configuration

Customize the server host, port, template directory, and underlying server options.

## Basic Usage

```python
from func_to_web import run

def my_function(x: int):
    return x * 2

# Single function
run(my_function, host="127.0.0.1", port=5000)

# Multiple functions with custom path
run([func1, func2], root_path="/my-tool")
```

## Parameters

- `func_or_list` - Single function or list of functions to serve.
- `host` - Server host (default: `"0.0.0.0"`).
- `port` - Server port (default: `8000`).
- `auth` - Dictionary of users/passwords for authentication (see [Authentication](authentication.md)).
- `secret_key` - Key for signing session cookies (see [Authentication](authentication.md)).
- `template_dir` - Custom template directory (optional).
- `root_path` - URL prefix for running behind a reverse proxy (default: `""`).
- `fastapi_config` - Dictionary with extra options for the FastAPI app (e.g., title, version).
- `**kwargs` - Extra options passed directly to the Uvicorn server configuration (SSL, workers, timeouts, etc.).

## Common Configurations

### Network Settings

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

### Reverse Proxy Configuration (Docker/Nginx)

If you are hosting your app behind a reverse proxy (like Nginx or Traefik) under a specific path (e.g., `https://domain.com/tools/app`), use `root_path` to ensure links and static files work correctly:

```python
# App is served at /tools/app
run(my_function, root_path="/tools/app")
```

### Advanced Uvicorn Options (SSL, Workers, Limits)

You can pass any valid Uvicorn configuration argument as extra keyword arguments. These are passed directly to `uvicorn.Config`.

**Enable SSL (HTTPS):**

```python
run(
    my_function,
    port=443,
    ssl_keyfile="./key.pem",
    ssl_certfile="./cert.pem"
)
```

**Performance Tuning:**

```python
run(
    my_function,
    workers=4,                  # Number of worker processes
    limit_max_requests=10000,   # Restart worker after N requests
    timeout_keep_alive=60       # Keep-alive timeout
)
```

### Custom API Metadata

You can customize the underlying FastAPI application using `fastapi_config`:

```python
run(
    my_function,
    fastapi_config={
        "title": "Internal Tools",
        "version": "2.0.0",
        "docs_url": None  # Disable /docs endpoint
    }
)
```

### Custom Templates

```python
run(my_function, template_dir="my_custom_templates")
```

To use custom templates, copy the default templates from the `./func_to_web/templates/` directory and modify them as needed, then specify the path in `template_dir`. With custom templates, you can completely change the look and functionality of the web interface.

## That's It!

You've completed the func-to-web documentation. Check out the [examples folder](https://github.com/offerrall/FuncToWeb/tree/main/examples) for 20 complete, runnable examples.
