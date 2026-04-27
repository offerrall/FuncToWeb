import secrets

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader
from starlette.middleware.sessions import SessionMiddleware

from .constants import TEMPLATES_DIR


_jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    auto_reload=False
)


def setup_auth(
    app: FastAPI,
    auth: dict[str, str],
    secret_key: str | None = None
) -> None:
    """Enable simple session-based authentication.

    Protects all routes except /login, /auth, /logout, /static, /front and /assets.
    Unauthenticated requests are redirected to /login (or return 401 for JSON).

    Registers:
    - /login  → login page
    - /auth   → credential check
    - /logout → clear session
    """
    key = secret_key or secrets.token_hex(32)

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        path = request.url.path

        if (
            path in ["/login", "/auth", "/logout"]
            or path.startswith("/static")
            or path.startswith("/front")
            or path.startswith("/assets")
        ):
            return await call_next(request)

        # Require session for protected routes.
        if not request.session.get("user"):
            if "application/json" in request.headers.get("accept", ""):
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            return RedirectResponse(url="/login")

        return await call_next(request)

    app.add_middleware(SessionMiddleware, secret_key=key, https_only=False)

    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        """Render login page."""
        if request.session.get("user"):
            return RedirectResponse(url="/")
        template = _jinja_env.get_template("login.html")
        return template.render(request=request)

    @app.post("/auth")
    async def authenticate(request: Request):
        """Validate credentials and create session."""
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")

            if (
                username in auth
                and password is not None
                and secrets.compare_digest(auth[username], password)
            ):
                request.session["user"] = username
                return RedirectResponse(url="/", status_code=303)

            template = _jinja_env.get_template("login.html")
            return HTMLResponse(
                template.render(request=request, error="Invalid credentials")
            )

        except Exception:
            template = _jinja_env.get_template("login.html")
            return HTMLResponse(
                template.render(request=request, error="Login failed")
            )

    @app.get("/logout")
    async def logout(request: Request):
        """Clear session and redirect to login."""
        request.session.clear()
        return RedirectResponse(url="/login")