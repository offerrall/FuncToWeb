# Server Configuration

Customize the server host, port, template directory, file storage, and underlying server options.

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
- `uploads_dir` - Directory for uploaded files (default: `"./uploads"`).
- `returns_dir` - Directory for returned files (default: `"./returned_files"`).
- `auto_delete_uploads` - If True, delete uploaded files after processing (default: `True`).
- `template_dir` - Custom template directory (optional).
- `root_path` - URL prefix for running behind a reverse proxy (default: `""`).
- `fastapi_config` - Dictionary with extra options for the FastAPI app (e.g., title, version).
- `**kwargs` - Extra options passed directly to Uvicorn. Any valid Uvicorn configuration option is supported.

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

### File Storage Configuration

**Default directories:**
```python
run(my_function)
# Uploaded files: ./uploads
# Returned files: ./returned_files
```

**Custom directories:**
```python
run(
    my_function,
    uploads_dir="/data/uploads",
    returns_dir="/data/returns"
)
```

**Upload file cleanup:**
```python
# Auto-delete uploads after processing (default)
run(my_function, auto_delete_uploads=True)

# Keep uploads (must clean manually)
run(my_function, auto_delete_uploads=False)
```

**Returned files lifecycle:**
- Files available for **1 hour** after creation (hardcoded)
- Cleanup runs on startup and every hour
- Not configurable (simplified design)

### Reverse Proxy Configuration (Docker/Nginx)

If you are hosting your app behind a reverse proxy (like Nginx or Traefik) under a specific path (e.g., `https://domain.com/tools/app`), use `root_path` to ensure links and static files work correctly:
```python
# App is served at /tools/app
run(my_function, root_path="/tools/app")
```

### Uvicorn Configuration Options

func-to-web passes all extra keyword arguments directly to Uvicorn. You can use any valid [Uvicorn configuration option](https://www.uvicorn.org/settings/).

**Examples:**
```python
# SSL/HTTPS
run(
    my_function,
    ssl_keyfile="./key.pem",
    ssl_certfile="./cert.pem"
)

# Performance tuning
run(
    my_function,
    limit_max_requests=10000,
    timeout_keep_alive=60,
    limit_concurrency=200
)

# Logging
run(
    my_function,
    log_level="debug",
    access_log=True
)

# Any Uvicorn option works
run(
    my_function,
    workers=4,
    reload=True,
    proxy_headers=True
)
```

See [Uvicorn documentation](https://www.uvicorn.org/settings/) for all available options.

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

## Production Example

Complete production setup:
```python
import os
from func_to_web import run

run(
    my_functions,
    host="127.0.0.1",
    port=8000,
    auth={"admin": os.environ["ADMIN_PASSWORD"]},
    secret_key=os.environ["SECRET_KEY"],
    uploads_dir="/data/uploads",
    returns_dir="/data/returns",
    auto_delete_uploads=True,
    root_path="/tools/my-app",
    ssl_keyfile="/etc/ssl/key.pem",
    ssl_certfile="/etc/ssl/cert.pem",
    fastapi_config={
        "title": "Production Tools",
        "version": "1.0.0"
    }
)
```

## That's It!

You've completed the func-to-web documentation. Check out the [examples folder](https://github.com/offerrall/FuncToWeb/tree/main/examples) for 20 complete, runnable examples.