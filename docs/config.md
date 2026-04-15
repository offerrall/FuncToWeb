# Server Configuration

FuncToWeb runs a FastAPI/Uvicorn server. The recommended setup is binding to `127.0.0.1` and letting Nginx act as reverse proxy

## Basic

```python
from func_to_web import run

run(my_function, host="127.0.0.1", port=8000)
```

## All Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `host` | `"0.0.0.0"` | Server host |
| `port` | `8000` | Server port |
| `auth` | `None` | `{username: password}` dict |
| `secret_key` | auto | Session signing key |
| `app_title` | auto | Page title |
| `css_vars` | `None` | CSS variable overrides |
| `favicon` | `None` | Path to favicon file |
| `uploads_dir` | `"./uploads"` | Uploaded files directory |
| `max_file_size` | `None` | Max upload size in bytes |
| `keep_uploads` | `False` | Keep uploads after execution |
| `returns_dir` | `"./returned_files"` | Returned files directory |
| `returns_lifetime` | `3600` | Seconds before returned files are deleted |
| `stream_prints` | `True` | Stream `print()` to browser |
| `root_path` | `""` | URL prefix for reverse proxy |
| `fastapi_config` | `None` | Extra FastAPI options |
| `**uvicorn_kwargs` | — | Any Uvicorn option |

Any option supported by Uvicorn or FastAPI can be passed through — `fastapi_config` for FastAPI constructor kwargs, and `**uvicorn_kwargs` for everything else.

## Common Setups

**Localhost only:**
```python
run(my_function, host="127.0.0.1")
```

**Custom port:**
```python
run(my_function, port=5000)
```

**Reverse proxy with path prefix:**
```python
run(my_function, root_path="/tools/my-app")
```

## Nginx + Supervisor

The recommended setup: Supervisor keeps the process alive, Nginx handles SSL termination and proxies to FuncToWeb on localhost. Set `root_path` to match the Nginx location, and disable proxy buffering if you use `stream_prints=True`.

## Production Example

```python
import os
from func_to_web import run

run(
    my_functions,
    host="127.0.0.1",
    port=8000,
    auth={"admin": os.environ["ADMIN_PASSWORD"]},
    secret_key=os.environ["SECRET_KEY"],
)
```