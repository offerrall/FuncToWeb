import qrcode
from func_to_web import run

def make_qr(text: str = "https://example.com"):
    return qrcode.make(text).get_image()

run(make_qr)
