# Server Configuration

Customize the server host, port, template directory, file cleanup, and underlying server options.

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
- `db_location` - Directory or path for the SQLite database (default: current working directory).
- `cleanup_hours` - Auto-cleanup files older than this many hours (default: `24`). Cleanup runs on startup and then every hour while server runs. Set to `0` to disable.
- `fastapi_config` - Dictionary with extra options for the FastAPI app (e.g., title, version).
- `**kwargs` - Extra options passed directly to the Uvicorn server configuration (SSL, timeouts, etc.).

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

### File Cleanup Configuration

**Default behavior (24-hour retention):**
```python
run(my_function)
```

**Custom retention period (6 hours):**
```python
run(my_function, cleanup_hours=6)
```

**Disable automatic cleanup:**
```python
run(my_function, cleanup_hours=0)
```

**Custom database location:**
```python
# Store in specific directory
run(my_function, db_location="/var/data/my_app")

# Store in temporary directory (cleaned by OS)
import tempfile
run(my_function, db_location=tempfile.gettempdir())

# Default: current working directory
run(my_function)  # Creates func_to_web.db in current dir
```

### Reverse Proxy Configuration (Docker/Nginx)

If you are hosting your app behind a reverse proxy (like Nginx or Traefik) under a specific path (e.g., `https://domain.com/tools/app`), use `root_path` to ensure links and static files work correctly:
```python
# App is served at /tools/app
run(my_function, root_path="/tools/app")
```

### Advanced Uvicorn Options (SSL, Timeouts)

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
    limit_max_requests=10000,   # Restart worker after N requests
    timeout_keep_alive=60       # Keep-alive timeout
)
```

**Note:** Multiple workers (`workers > 1`) are **not supported**. See [Scaling](#scaling-guidelines) below.

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

## Scaling Guidelines

### Why Multiple Workers Are Not Supported

func-to-web uses SQLite for file tracking, which is not designed for concurrent writes across multiple processes. Attempting to use `workers > 1` will raise an error:
```python
# ❌ This will raise ValueError
run(my_function, workers=4)
```

**Error message:**
```
ValueError: func-to-web does not support multiple workers (workers > 1)

Reason: SQLite-based file tracking is not designed for concurrent
        writes across multiple processes.

For scaling:
  • Single worker can handle 500-1000 req/s with async I/O
  • For higher loads, run multiple instances
```

### Single Worker Performance

A single worker can handle:
- ✅ **500-1,000 requests/second** for I/O-bound operations
- ✅ **50-100 concurrent users** with async operations
- ✅ **GB+ file uploads/downloads** via streaming

**Sufficient for:**
- Internal team dashboards (5-50 users)
- Admin panels and internal tools
- Data science workflows
- Prototyping and MVPs

### Scaling with Multiple Instances

For higher loads, run multiple instances on different ports behind a load balancer:

**Step 1: Run instances on different ports**
```bash
# Terminal 1
python app.py --port 8001 --db-location /data/instance1

# Terminal 2
python app.py --port 8002 --db-location /data/instance2

# Terminal 3
python app.py --port 8003 --db-location /data/instance3
```

**Step 2: Configure Nginx with sticky sessions**
```nginx
upstream func_to_web {
    ip_hash;  # Sticky sessions - same user → same backend
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name myapp.example.com;
    
    location / {
        proxy_pass http://func_to_web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Why sticky sessions?** Each instance has its own SQLite database. Users must be routed to the same instance to download their generated files.

### Limitations of Multiple Instances

- **IP change**: If user's IP changes (WiFi → 4G), they may lose access to files
- **Instance crash**: If an instance crashes, files on that instance become unavailable
- **Not suitable**: For >1,000 concurrent users or distributed systems

### Enterprise Scaling

For very high loads (1,000+ concurrent users), consider:
- FastAPI + Celery + Redis + PostgreSQL
- Shared storage (NFS/EFS) with coordination layer
- Microservices architecture

func-to-web is optimized for team-scale applications, not Twitter-scale systems.

## Production Example

Complete production setup with all options:
```python
import os
from pathlib import Path
from func_to_web import run

run(
    my_functions,
    host="127.0.0.1",                           # Behind Nginx
    port=8000,
    auth={"admin": os.environ["ADMIN_PASSWORD"]},
    secret_key=os.environ["SECRET_KEY"],
    root_path="/tools/my-app",                  # Reverse proxy path
    db_location="/var/data/func_to_web",        # Persistent data
    cleanup_hours=48,                           # 2-day retention
    fastapi_config={
        "title": "Production Tools",
        "version": "1.0.0"
    }
)
```

## Summary

func-to-web is designed for **simplicity and reliability** in team-scale applications:

✅ **Single worker**: Handles 500-1,000 req/s  
✅ **Multiple instances**: Scale horizontally with Nginx  
✅ **Team-scale**: Optimized for 5-100 concurrent users  
⚠️ **Not Twitter-scale**: For massive loads, use FastAPI + Redis

**Note:** The architecture prioritizes ease of use and reliability over maximum scalability. For most teams, single-worker performance is more than sufficient.

## That's It!

You've completed the func-to-web documentation. Check out the [examples folder](https://github.com/offerrall/FuncToWeb/tree/main/examples) for 20 complete, runnable examples.