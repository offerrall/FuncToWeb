from func_to_web import run
from func_to_web.types import Email

def subscribe(contact: Email):
    return f"Subscribed: {contact}"

run(subscribe)
