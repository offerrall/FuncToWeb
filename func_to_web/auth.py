import secrets
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware


def setup_auth_middleware(
    app, auth: dict[str, str], templates: Jinja2Templates, secret_key: str | None = None
):
    """Setup authentication middleware and routes.

    Args:
        app: FastAPI application instance.
        auth: Dictionary of {username: password} for authentication.
        templates: Jinja2Templates instance.
        secret_key: Secret key for session signing.
    """
    key = secret_key or secrets.token_hex(32)

    def _root_path(request: Request):
        root_path = request.scope.get("root_path", "") or ""
        if root_path.endswith("/"):
            root_path = root_path[:-1]
        return root_path

    def _with_root_path(request: Request, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{_root_path(request)}{path}"

    # 1. Define Auth Middleware (INNER)
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        path = request.url.path.removeprefix(_root_path(request))
        # Allow public paths: login page, auth endpoint, and static assets
        if path in ["/login", "/auth"] or path.startswith("/static"):
            return await call_next(request)

        # Check for valid session
        if not request.session.get("user"):
            # If API call (AJAX), return 401
            if "application/json" in request.headers.get("accept", ""):
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            # If browser navigation, redirect to login
            return RedirectResponse(url=_with_root_path(request, "/login"))

        return await call_next(request)

    # 2. Add SessionMiddleware (OUTER - runs first)
    app.add_middleware(SessionMiddleware, secret_key=key, https_only=False)

    @app.get("/login")
    async def login_page(request: Request):
        # If already logged in, go home
        if request.session.get("user"):
            return RedirectResponse(url=_with_root_path(request, "/"))
        return templates.TemplateResponse("login.html", {"request": request})

    @app.post("/auth")
    async def authenticate(request: Request):
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")

            if username in auth:
                # Safe comparison against Timing Attacks
                if secrets.compare_digest(auth[username], password):
                    request.session["user"] = username
                    return RedirectResponse(
                        url=_with_root_path(request, "/"), status_code=303
                    )

            return templates.TemplateResponse(
                "login.html", {"request": request, "error": "Invalid credentials"}
            )
        except Exception:
            return templates.TemplateResponse(
                "login.html", {"request": request, "error": "Login failed"}
            )

    @app.get("/logout")
    async def logout(request: Request):
        request.session.clear()
        return RedirectResponse(url=_with_root_path(request, "/login"))
