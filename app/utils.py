import qrcode
from pathlib import Path


def generate_qr_code(path, file_name):
    img = qrcode.make(path)
    downloads_path = str(Path.home() / "Downloads")
    img.save(downloads_path + f"/{file_name}.png")
    