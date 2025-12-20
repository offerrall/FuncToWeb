import subprocess
from typing import Literal
from func_to_web import run

# 🔒 MANDATORY: Use HTTPS (Nginx).

def restart_service(service: Literal['nginx', 'gunicorn', 'celery']):
    """Restarts a system service."""
    # check=True raises an error shown in the Web UI if the command fails
    subprocess.run(["sudo", "supervisorctl", "restart", service], check=True)
    return f"✅ Service {service} restarted."

run(restart_service, auth={"admin": "super_secret_password"})