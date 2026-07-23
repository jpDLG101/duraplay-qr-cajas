import qrcode

def generate(identifier: str):
    return qrcode.make(identifier)