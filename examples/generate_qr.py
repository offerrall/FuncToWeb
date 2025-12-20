import qrcode
from func_to_web import run

def make_qr(text: str):
    """Returns a QR code image for the given text."""
    return qrcode.make(text).get_image()

run(make_qr)