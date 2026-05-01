from func_to_web import run

def admin_panel(action: str):
    return f"Admin executed: {action}"

run(admin_panel, auth={"admin": "change_me_in_production"})
