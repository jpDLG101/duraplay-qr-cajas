from pathlib import Path

def export(img, identifier: str, folder: Path) -> Path:
    target_path = folder / f"{identifier}.png"
    img.save(target_path)
    return target_path