from func_to_web import run

def toggle(active: bool = True, verbose: bool = False):
    return f"active={active}, verbose={verbose}"

run(toggle)
