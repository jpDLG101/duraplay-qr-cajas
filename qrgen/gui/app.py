import queue
import sys
import threading
import tkinter as tk

from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from qrgen.core.parser import parse
from qrgen.core.deduplicator import deduplicate
from qrgen.core.generator import generate
from qrgen.core.exporter import export
from qrgen.io.csv_reader import read_csv, read_headers
from qrgen.gui.os_utils import open_folder, reveal_file
from qrgen.gui.theme import ThemeController, load_logo, load_icon_images

WINDOW_MIN_WIDTH = 680
NO_COLUMN = "Selecciona columna"
MAX_ERRORS_SHOWN = 10

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
            icon_images = load_icon_images(base_path)
            root.iconphoto(True, *icon_images)
            root._icon_images = icon_images
        except Exception:
            pass

    theme = ThemeController(root)
    colors = theme.colors
    root.configure(background=colors["bg"])

    logo_photo = load_logo(base_path, theme.dark_mode)

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

    def _update_logo():
        new_logo = load_logo(base_path, theme.dark_mode)
        logo_label.config(image=new_logo)
        logo_label.image = new_logo

    theme.on_change(_update_logo)

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
    manual_frame.grid(row=1, column=0, columnspan=2, sticky="new", pady=(8, 0))
    manual_frame.columnconfigure(0, weight=1)
    ttk.Label(manual_frame, text="Un código de caja por línea (o separados por coma):").grid(
        row=0, column=0, sticky="w"
    )
    text_input_border = tk.Frame(manual_frame, background=colors["border"])
    text_input_border.grid(row=1, column=0, sticky="ew", pady=(4, 0))
    text_input_border.columnconfigure(0, weight=1)

    text_input = tk.Text(
        text_input_border, height=4, wrap="word",
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

    theme.on_change(_reapply_text_input_colors)

    csv_frame = ttk.Frame(ident_frame)
    csv_frame.grid(row=1, column=0, columnspan=2, sticky="new", pady=(8, 0))
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
    csv_column_menu = ttk.Combobox(csv_frame, textvariable=csv_column_var, state="readonly")
    csv_column_menu.grid(row=1, column=1, sticky="ew", padx=8, pady=4)

    ident_frame.update_idletasks()
    shared_row_height = max(manual_frame.winfo_reqheight(), csv_frame.winfo_reqheight()) + 10
    shared_row_width = max(manual_frame.winfo_reqwidth(), csv_frame.winfo_reqwidth())
    ident_frame.grid_rowconfigure(1, minsize=shared_row_height)

    width_spacer = tk.Frame(ident_frame, height=1, width=shared_row_width, background=colors["bg"])
    width_spacer.grid(row=2, column=0, columnspan=2, sticky="ew")

    def _reapply_width_spacer_color():
        width_spacer.config(background=colors["bg"])

    theme.on_change(_reapply_width_spacer_color)

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
        csv_column_menu["values"] = headers
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

        total = len(idents)
        progress_queue: queue.Queue = queue.Queue()

        def worker():
            generated_files: list[Path] = []
            error_messages: list[str] = []
            for i, ident in enumerate(idents, start=1):
                try:
                    generated_files.append(export(generate(ident), ident, folder))
                except Exception as e:
                    error_messages.append(f"{ident}: {e}")
                progress_queue.put(("progress", i, total))
            progress_queue.put(("done", generated_files, error_messages))

        threading.Thread(target=worker, daemon=True).start()

        def finish_generation(generated_files, error_messages):
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
                btn_open_file.config(command=lambda: open_folder(file))
                btn_open_file.grid(row=0, column=0, sticky="ew", padx=(0, 4))
                btn_open_folder.config(command=lambda: reveal_file(file), style="TButton")
                btn_open_folder.grid(row=0, column=1, sticky="ew", padx=(4, 0))
                result_frame.grid()
            elif generated_files:
                btn_open_file.grid_remove()
                btn_open_folder.config(command=lambda: open_folder(folder), style="Accent.TButton")
                btn_open_folder.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0)
                result_frame.grid()
            else:
                result_frame.grid_remove()

            root.update_idletasks()
            messagebox.showinfo("Completado...", report)

        def poll_generation_queue():
            latest_progress = None
            done_message = None
            try:
                while True:
                    message = progress_queue.get_nowait()
                    if message[0] == "progress":
                        latest_progress = message
                    elif message[0] == "done":
                        done_message = message
            except queue.Empty:
                pass

            if latest_progress:
                _, i, i_total = latest_progress
                progress.config(value=i)
                status_var.set(f"Generando {i}/{i_total}...")

            if done_message:
                _, generated_files, error_messages = done_message
                finish_generation(generated_files, error_messages)
                return

            root.after(50, poll_generation_queue)

        root.after(50, poll_generation_queue)

    #trace de la app
    source_var.trace_add("write", on_mode_change)
    on_mode_change()

    theme.start_polling()
    root.mainloop()
