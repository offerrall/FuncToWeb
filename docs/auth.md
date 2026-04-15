# Authentication

Protect your app with username/password authentication:

```python
from func_to_web import run

def admin_tool(action: str): return f"Done: {action}"

run(admin_tool, auth={"admin": "secure_password"})
```

Users must log in before accessing any function. Sessions are maintained via signed cookies — no database required.

## Multiple Users

```python
run(
    my_function,
    auth={
        "admin":   "strong_password_1",
        "analyst": "strong_password_2",
    }
)
```

All authenticated users have full access. Implement role-based logic inside your functions if needed.

## Secret Key

FuncToWeb auto-generates a secret key for signing session cookies. Set one explicitly to keep sessions valid across restarts:

```python
import os
run(
    my_function,
    auth={"admin": os.environ["ADMIN_PASSWORD"]},
    secret_key=os.environ["SECRET_KEY"],
)
```

## Session Lifetime

Sessions last 2 weeks by default. Users stay logged in across browser restarts.

## Security Notes

- Always use **HTTPS** in production — without it, session cookies can be intercepted
- Use **strong, unique passwords** (16+ random characters)

> For production deployments, see [Server Configuration](config.md).
