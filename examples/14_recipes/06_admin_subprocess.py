import subprocess
from typing import Literal
from func_to_web import run

def restart_service(service: Literal["nginx", "gunicorn", "celery"]):
    """Restart a system service (requires sudo and supervisorctl)."""
    result = subprocess.run(
        ["sudo", "supervisorctl", "restart", service],
        capture_output=True,
        text=True,
    )
    return f"{service}: {result.stdout or result.stderr}"

run(restart_service, auth={"admin": "change_me"})
