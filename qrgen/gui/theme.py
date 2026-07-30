import subprocess
import sys
import tkinter as tk

import sv_ttk

from pathlib import Path
from PIL import Image, ImageTk

LOGO_HEIGHT_PX = 52

ICON_DIR_NAME = "icon.iconset"
ICON_FILENAMES = (
    "icon_16x16.png", "icon_16x16@2x.png",
    "icon_32x32.png", "icon_32x32@2x.png",
    "icon_128x128.png", "icon_128x128@2x.png",
    "icon_256x256.png", "icon_256x256@2x.png",
    "icon_512x512.png", "icon_512x512@2x.png",
)


def is_dark_mode() -> bool:
    try:
        if sys.platform == "darwin":
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=2,
            )
            return "dark" in result.stdout.lower()
        elif sys.platform == "win32":
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
    except Exception:
        pass
    return False


def theme_colors(dark_mode: bool) -> dict:
    return {
        "bg": "#1c1c1c" if dark_mode else "#fafafa",
        "fg": "#fafafa" if dark_mode else "#1c1c1c",
        "field_bg": "#292929" if dark_mode else "#fdfdfd",
        "border": "#454545" if dark_mode else "#c6c6c6",
        "muted_fg": "#595959" if dark_mode else "#a0a0a0",
        "select_bg": "#2f60d8",
        "select_fg": "#ffffff",
    }


def load_logo(base_path: Path, dark_mode: bool) -> ImageTk.PhotoImage:
    logo_filename = "logotipo-hdr@3x_darkmode.png" if dark_mode else "logotipo-hdr@3x.png"
    logo_img = Image.open(base_path / "assets" / logo_filename).convert("RGBA")
    bbox = logo_img.getbbox()
    if bbox:
        logo_img = logo_img.crop(bbox)
    ratio = LOGO_HEIGHT_PX / logo_img.height
    logo_img = logo_img.resize((int(logo_img.width * ratio), LOGO_HEIGHT_PX))
    return ImageTk.PhotoImage(logo_img)


def load_icon_images(base_path: Path) -> list[tk.PhotoImage]:
    icon_dir = base_path / "assets" / ICON_DIR_NAME
    return [tk.PhotoImage(file=str(icon_dir / name)) for name in ICON_FILENAMES]


class ThemeController:

    POLL_INTERVAL_MS = 1000
    REAPPLY_DELAY_MS = 200

    def __init__(self, root: tk.Tk):
        self.root = root
        self.dark_mode = is_dark_mode()
        self.colors = theme_colors(self.dark_mode)
        self._on_change_callbacks = []
        sv_ttk.set_theme("dark" if self.dark_mode else "light")
        self.root.after(self.REAPPLY_DELAY_MS, self._run_callbacks)

    def on_change(self, callback) -> None:
        """Registra una funcion para correr cuando cambia el tema (con retraso)."""
        self._on_change_callbacks.append(callback)

    def start_polling(self) -> None:
        self.root.after(self.POLL_INTERVAL_MS, self._poll)

    def _poll(self) -> None:
        new_dark = is_dark_mode()
        if new_dark != self.dark_mode:
            self.dark_mode = new_dark
            sv_ttk.set_theme("dark" if new_dark else "light")
            self.colors.update(theme_colors(new_dark))
            self.root.after(self.REAPPLY_DELAY_MS, self._run_callbacks)
        self.root.after(self.POLL_INTERVAL_MS, self._poll)

    def _run_callbacks(self) -> None:
        for callback in self._on_change_callbacks:
            callback()
