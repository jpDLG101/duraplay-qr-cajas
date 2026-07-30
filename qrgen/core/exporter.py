import re

from pathlib import Path

ILLEGAL_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')

def export(img, identifier: str, folder: Path) -> Path:
    safe_name = ILLEGAL_FILENAME_CHARS.sub("_", identifier)
    target_path = folder / f"{safe_name}.png"
    img.save(target_path)
    return target_path
