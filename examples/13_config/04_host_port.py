from func_to_web import run

def ping():
    return "pong"

run(ping, host="127.0.0.1", port=5000)
