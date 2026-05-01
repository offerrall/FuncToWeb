from func_to_web import run

def shared_tool(message: str):
    return f"Message: {message}"

run(
    shared_tool,
    auth={
        "admin":   "strong_password_1",
        "analyst": "strong_password_2",
    },
)
