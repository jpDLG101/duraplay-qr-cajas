import os
import subprocess
import sys

from pathlib import Path


def open_folder(path: Path) -> None:
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)])
        elif sys.platform == "win32":
            os.startfile(str(path))
        else:
            subprocess.run(["xdg-open", str(path)])
    except Exception:
        pass


def reveal_file(path: Path) -> None:
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", str(path)])
        elif sys.platform == "win32":
            subprocess.run(["explorer", f"/select,{str(path)}"])
        else:
            open_folder(path.parent)
    except Exception:
        pass
