from func_to_web import run, HiddenFunction

def public_tool(text: str):
    return f"Public: {text}"

def internal_tool(token: str):
    return f"Internal call with token={token}"

# internal_tool is not in the index, but is reachable at /internal-tool
run([public_tool, HiddenFunction(internal_tool)])
