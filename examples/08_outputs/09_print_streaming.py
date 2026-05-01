import time
from func_to_web import run

def long_task(steps: int = 5):
    for i in range(1, steps + 1):
        print(f"Processing step {i}/{steps}...")
        time.sleep(0.5)
    return "All done!"

run(long_task)
