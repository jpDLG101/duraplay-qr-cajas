import os
import subprocess
import sys
import tkinter as tk

import sv_ttk

from PIL import Image, ImageTk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from qrgen.core.parser import parse
from qrgen.core.deduplicator import deduplicate
from qrgen.core.generator import generate
from qrgen.core.exporter import export
from qrgen.io.csv_reader import read_csv, read_headers

WINDOW_MIN_WIDTH = 680
LOGO_HEIGHT_PX = 52
NO_COLUMN = "Selecciona columna"
MAX_ERRORS_SHOWN = 10
PROGRESS_UPDATE_STRIDE = 5

ICON_DIR_NAME = "icon.iconset"
ICON_FILENAMES = (
    "icon_16x16.png", "icon_16x16@2x.png",
    "icon_32x32.png", "icon_32x32@2x.png",
    "icon_128x128.png", "icon_128x128@2x.png",
    "icon_256x256.png", "icon_256x256@2x.png",
    "icon_512x512.png", "icon_512x512@2x.png",
)

def _is_dark_mode() -> bool:
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


def _open_folder(path: Path) -> None:
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)])
        elif sys.platform == "win32":
            os.startfile(str(path))
        else:
            subprocess.run(["xdg-open", str(path)])
    except Exception:
        pass


def _reveal_file(path: Path) -> None:
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", str(path)])
        elif sys.platform == "win32":
            subprocess.run(["explorer", f"/select,{str(path)}"])
        else:
            _open_folder(path.parent)
    except Exception:
        pass


def _load_icon_images(base_path: Path) -> list[tk.PhotoImage]:
    icon_dir = base_path / "assets" / ICON_DIR_NAME
    return [tk.PhotoImage(file=str(icon_dir / name)) for name in ICON_FILENAMES]


def _theme_colors(dark_mode: bool) -> dict:
    return {
        "bg": "#1c1c1c" if dark_mode else "#fafafa",
        "fg": "#fafafa" if dark_mode else "#1c1c1c",
        "field_bg": "#292929" if dark_mode else "#fdfdfd",
        "border": "#454545" if dark_mode else "#c6c6c6",
        "muted_fg": "#595959" if dark_mode else "#a0a0a0",
        "select_bg": "#2f60d8",
        "select_fg": "#ffffff",
    }


def _load_logo(base_path: Path, dark_mode: bool) -> ImageTk.PhotoImage:
    logo_filename = "logotipo-hdr@3x_darkmode.png" if dark_mode else "logotipo-hdr@3x.png"
    logo_img = Image.open(base_path / "assets" / logo_filename).convert("RGBA")
    #las dos variantes traen distinto margen transparente alrededor de la
    #marca; se recorta al contenido real antes de escalar para que ambas
    #terminen del mismo tamaño visual
    bbox = logo_img.getbbox()
    if bbox:
        logo_img = logo_img.crop(bbox)
    ratio = LOGO_HEIGHT_PX / logo_img.height
    logo_img = logo_img.resize((int(logo_img.width * ratio), LOGO_HEIGHT_PX))
    return ImageTk.PhotoImage(logo_img)


def run() -> None:
    #window
    root = tk.Tk()
    root.title("Duraplay QR Cajas")
    root.minsize(WINDOW_MIN_WIDTH, 0)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    base_path = Path(__file__).parent.parent.parent

    skip_iconphoto = sys.platform == "darwin" and getattr(sys, "frozen", False)
    if not skip_iconphoto:
        try:
            icon_images = _load_icon_images(base_path)
            root.iconphoto(True, *icon_images)
            root._icon_images = icon_images
        except Exception:
            pass

    dark_mode = _is_dark_mode()
    #lista de un elemento: las funciones internas no pueden reasignar
    #variables del scope externo directamente, pero si pueden mutar una lista
    current_theme = ["dark" if dark_mode else "light"]
    sv_ttk.set_theme(current_theme[0])
    colors = _theme_colors(dark_mode)
    root.configure(background=colors["bg"])

    logo_photo = _load_logo(base_path, dark_mode)

    source_var = tk.StringVar(value="manual")
    csv_column_var = tk.StringVar(value=NO_COLUMN)
    output_path_var = tk.StringVar(value="")
    status_var = tk.StringVar(value="")

    #layout base
    main = ttk.Frame(root, padding=16)
    main.grid(row=0, column=0, sticky="nsew")
    main.columnconfigure(0, weight=1)

    #logo
    logo_label = ttk.Label(main, image=logo_photo)
    logo_label.image = logo_photo
    logo_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

    subtitle_label = ttk.Label(
        main,
        text="Generación de los códigos QR para las cajas de los camiones.",
        foreground=colors["muted_fg"],
    )
    subtitle_label.grid(row=1, column=0, sticky="w", pady=(0, 12))

    #seccion: identificadores
    ident_frame = ttk.LabelFrame(main, text="Códigos de las cajas", padding=12)
    ident_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
    ident_frame.columnconfigure(0, weight=1)
    ident_frame.columnconfigure(1, weight=1)

    rb_manual = ttk.Radiobutton(ident_frame, text="Escribir códigos", variable=source_var, value="manual")
    rb_csv    = ttk.Radiobutton(ident_frame, text="Importar de la base de datos (CSV)", variable=source_var, value="csv")
    rb_manual.grid(row=0, column=0, sticky="w")
    rb_csv.grid(row=0, column=1, sticky="w")

    manual_frame = ttk.Frame(ident_frame)
    manual_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    manual_frame.columnconfigure(0, weight=1)
    ttk.Label(manual_frame, text="Un código de caja por línea (o separados por coma):").grid(
        row=0, column=0, sticky="w"
    )
    text_input_border = tk.Frame(manual_frame, background=colors["border"])
    text_input_border.grid(row=1, column=0, sticky="ew", pady=(4, 0))
    text_input_border.columnconfigure(0, weight=1)

    text_input = tk.Text(
        text_input_border, height=6, wrap="word",
        background=colors["field_bg"], foreground=colors["fg"],
        insertbackground=colors["fg"],
        selectbackground=colors["select_bg"], selectforeground=colors["select_fg"],
        relief="flat", borderwidth=0, highlightthickness=0,
    )
    text_input.grid(row=0, column=0, sticky="ew", padx=1, pady=1)

    def _reapply_text_input_colors():
        text_input_border.config(background=colors["border"])
        text_input.config(
            background=colors["field_bg"], foreground=colors["fg"],
            insertbackground=colors["fg"],
            selectbackground=colors["select_bg"], selectforeground=colors["select_fg"],
        )

    root.after(200, _reapply_text_input_colors)

    def _poll_theme():
        new_dark = _is_dark_mode()
        new_theme = "dark" if new_dark else "light"
        if new_theme != current_theme[0]:
            sv_ttk.set_theme(new_theme)
            current_theme[0] = new_theme
            colors.update(_theme_colors(new_dark))
            root.after(200, _reapply_text_input_colors)
            new_logo = _load_logo(base_path, new_dark)
            logo_label.config(image=new_logo)
            logo_label.image = new_logo
        root.after(1000, _poll_theme)

    csv_frame = ttk.Frame(ident_frame)
    csv_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    csv_frame.columnconfigure(1, weight=1)

    ttk.Label(csv_frame, text="Archivo CSV (exportado de la base de datos):").grid(
        row=0, column=0, sticky="w", pady=4
    )
    csv_path_var = tk.StringVar(value="")
    csv_path_entry = ttk.Entry(csv_frame, textvariable=csv_path_var, state="readonly")
    csv_path_entry.grid(row=0, column=1, sticky="ew", padx=8, pady=4)
    btn_browse_csv = ttk.Button(csv_frame, text="Examinar…", command=lambda: browse_csv())
    btn_browse_csv.grid(row=0, column=2, pady=4)

    ttk.Label(csv_frame, text="Columna con el código:").grid(row=1, column=0, sticky="w", pady=4)
    csv_column_menu = tk.OptionMenu(csv_frame, csv_column_var, NO_COLUMN)
    csv_column_menu.grid(row=1, column=1, sticky="ew", padx=8, pady=4)
    csv_column_menu.configure(
        background=colors["field_bg"], foreground=colors["fg"],
        activebackground=colors["select_bg"], activeforeground=colors["select_fg"],
        relief="flat", borderwidth=1, highlightthickness=0,
    )
    csv_column_menu["menu"].configure(
        background=colors["field_bg"], foreground=colors["fg"],
        activebackground=colors["select_bg"], activeforeground=colors["select_fg"],
    )

    #seccion: salida
    output_frame = ttk.LabelFrame(main, text="Carpeta de salida", padding=12)
    output_frame.grid(row=3, column=0, sticky="ew", pady=(0, 12))
    output_frame.columnconfigure(1, weight=1)

    ttk.Label(output_frame, text="Guardar los QR en:").grid(row=0, column=0, sticky="w")
    output_entry = ttk.Entry(output_frame, textvariable=output_path_var, state="readonly")
    output_entry.grid(row=0, column=1, sticky="ew", padx=8)
    btn_browse_output = ttk.Button(output_frame, text="Examinar…", command=lambda: browse_output())
    btn_browse_output.grid(row=0, column=2)

    #fila de accion
    action_frame = ttk.Frame(main)
    action_frame.grid(row=4, column=0, sticky="ew")
    action_frame.columnconfigure(0, weight=1)

    status_label = ttk.Label(action_frame, textvariable=status_var, foreground=colors["muted_fg"])
    status_label.grid(row=0, column=0, sticky="w")

    btn_generate = ttk.Button(action_frame, text="Generar QR", style="Accent.TButton", command=lambda: on_generate())
    btn_generate.grid(row=0, column=1, sticky="e")

    progress = ttk.Progressbar(main, orient="horizontal", mode="determinate")
    progress.grid(row=5, column=0, sticky="ew", pady=(8, 0))
    progress.grid_remove()

    result_frame = ttk.Frame(main)
    result_frame.grid(row=6, column=0, sticky="ew", pady=(8, 0))
    result_frame.columnconfigure(0, weight=1)
    result_frame.columnconfigure(1, weight=1)

    btn_open_file = ttk.Button(result_frame, text="Abrir imagen", style="Accent.TButton")
    btn_open_file.grid(row=0, column=0, sticky="ew", padx=(0, 4))
    btn_open_folder = ttk.Button(result_frame, text="Abrir carpeta")
    btn_open_folder.grid(row=0, column=1, sticky="ew", padx=(4, 0))
    result_frame.grid_remove()

    #handlers
    def load_csv_columns(path_str):
        if not path_str:
            return
        try:
            headers = read_headers(Path(path_str))
        except Exception:
            return
        menu = csv_column_menu["menu"]
        menu.delete(0, tk.END)
        for col in headers:
            menu.add_command(label=col, command=lambda c=col: csv_column_var.set(c))
        if headers:
            csv_column_var.set(headers[0])

    def browse_csv():
        kwargs = {"filetypes": [("CSV files", "*.csv"), ("All files", "*.*")]}
        if csv_path_var.get():
            kwargs["initialdir"] = str(Path(csv_path_var.get()).parent)
        file = filedialog.askopenfilename(**kwargs)
        if not file:
            return
        csv_path_var.set(file)
        csv_path_entry.xview_moveto(1)
        load_csv_columns(file)

    def browse_output():
        kwargs = {}
        if output_path_var.get():
            kwargs["initialdir"] = output_path_var.get()
        folder = filedialog.askdirectory(**kwargs)
        if folder:
            output_path_var.set(folder)
            output_entry.xview_moveto(1)

    def on_mode_change(*args):
        if source_var.get() == "manual":
            manual_frame.grid()
            csv_frame.grid_remove()
        else:
            csv_frame.grid()
            manual_frame.grid_remove()
                    
    def on_generate():
        if not output_path_var.get():
            messagebox.showwarning("Falta información", "Selecciona la carpeta donde guardar los QR antes de generar.")
            return

        if source_var.get() == "csv":
            if not csv_path_var.get() or csv_column_var.get() == NO_COLUMN:
                messagebox.showwarning(
                    "Falta información", "Selecciona el archivo CSV y la columna con el código antes de generar."
                )
                return

        try:
            if source_var.get() == "csv":
                identifiers = read_csv(Path(csv_path_var.get()), csv_column_var.get())
            else:
                identifiers = parse(text_input.get("1.0", tk.END))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron leer los códigos: {e}")
            return

        if not identifiers:
            messagebox.showwarning("Sin códigos", "No se encontró ningún código para generar.")
            return

        idents, dup = deduplicate(identifiers)
        folder = Path(output_path_var.get())
        folder.mkdir(parents=True, exist_ok=True)

        btn_generate.config(state="disabled", text="Generando...")
        result_frame.grid_remove()
        progress.grid()
        progress.config(maximum=len(idents), value=0)
        root.update_idletasks()

        error_messages = []
        total = len(idents)
        generated_files: list[Path] = []
        
        for i, ident in enumerate(idents, start=1):
            try:
                generated_files.append(export(generate(ident), ident, folder))
            except Exception as e:
                error_messages.append(f"{ident}: {e}")
            progress.config(value=i)
            status_var.set(f"Generando {i}/{total}...")
            if i % PROGRESS_UPDATE_STRIDE == 0 or i == total:
                root.update_idletasks()

        btn_generate.config(state="normal", text="Generar QR")
        status_var.set("Completado...")

        report = (
            f"{len(identifiers)} códigos recibidos\n"
            f"{len(idents)} QR generados\n"
            f"{dup} duplicados eliminados\n"
            f"{len(error_messages)} errores"
        )
        if error_messages:
            shown = error_messages[:MAX_ERRORS_SHOWN]
            report += "\n\n" + "\n".join(shown)
            if len(error_messages) > MAX_ERRORS_SHOWN:
                report += f"\n... y {len(error_messages) - MAX_ERRORS_SHOWN} más"
        
        if len(generated_files) == 1:
            file = generated_files[0]
            btn_open_file.config(command=lambda: _open_folder(file))
            btn_open_file.grid(row=0, column=0, sticky="ew", padx=(0, 4))
            btn_open_folder.config(command=lambda: _reveal_file(file), style="TButton")
            btn_open_folder.grid(row=0, column=1, sticky="ew", padx=(4, 0))
            result_frame.grid()
        elif generated_files:
            btn_open_file.grid_remove()
            btn_open_folder.config(command=lambda: _open_folder(folder), style="Accent.TButton")
            btn_open_folder.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0)
            result_frame.grid()
        else:
            result_frame.grid_remove()

        messagebox.showinfo("Completado...", report)

    #trace de la app
    source_var.trace_add("write", on_mode_change)
    on_mode_change()
    root.after(2000, _poll_theme)
    root.mainloop()
    
    
    
    