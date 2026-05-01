from func_to_web import run

def list_items(prefix: str = "item"):
    return [
        {"id": i, "name": f"{prefix}_{i}", "value": i * 10}
        for i in range(1, 21)
    ]

run(list_items)
