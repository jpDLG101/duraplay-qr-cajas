import tkinter as tk
from pathlib import Path
from tkinter import messagebox, filedialog

from qrgen.core.parser import parse
from qrgen.core.deduplicator import deduplicate
from qrgen.core.generator import generate
from qrgen.core.exporter import export
from qrgen.io.csv_reader import read_csv


def run() -> None:
    #window
    root = tk.Tk()
    root.title("QR Cajas")
    root.geometry("650x400")

    source_var = tk.StringVar(value="manual")

    #widgets
    label = tk.Label(root, text="Identificadores:")
    label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")

    rb_manual = tk.Radiobutton(root, text="Manual", variable=source_var, value="manual")
    rb_csv    = tk.Radiobutton(root, text="CSV",    variable=source_var, value="csv")
    rb_manual.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    rb_csv.grid(row=1, column=1, padx=10, pady=5, sticky="w")

    text_input = tk.Text(root, width=50, height=6)
    text_input.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

    csv_path_label = tk.Label(root, text="Archivo CSV:")
    csv_path_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
    csv_path_entry = tk.Entry(root, width=40)
    csv_path_entry.grid(row=3, column=1, padx=10, pady=5)
    btn_browse_csv = tk.Button(root, text="Examinar", command=lambda: browse_csv())
    btn_browse_csv.grid(row=3, column=2, padx=5)

    csv_column_label = tk.Label(root, text="Columna:")
    csv_column_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
    csv_column_entry = tk.Entry(root, width=40)
    csv_column_entry.grid(row=4, column=1, padx=10, pady=5)

    path_label = tk.Label(root, text="Carpeta destino:")
    path_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
    output_entry = tk.Entry(root, width=30)
    output_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")
    btn_browse_output = tk.Button(root, text="Examinar", command=lambda: browse_output())
    btn_browse_output.grid(row=5, column=2, padx=5)

    btn_generate = tk.Button(root, text="Generar QR", command=lambda: on_generate())
    btn_generate.grid(row=6, column=0, columnspan=2, pady=15)

    def browse_csv():
        file = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file:
            csv_path_entry.delete(0, tk.END)
            csv_path_entry.insert(0, file)

    def browse_output():
        folder = filedialog.askdirectory()
        if folder:
            output_entry.delete(0, tk.END)
            output_entry.insert(0, folder)

    def on_mode_change(*args):
        if source_var.get() == "manual":
            text_input.grid()
            csv_path_label.grid_remove()
            csv_path_entry.grid_remove()
            btn_browse_csv.grid_remove()
            csv_column_label.grid_remove()
            csv_column_entry.grid_remove()
        else:
            text_input.grid_remove()
            csv_path_label.grid()
            csv_path_entry.grid()
            btn_browse_csv.grid()
            csv_column_label.grid()
            csv_column_entry.grid()

    def on_generate():
        if source_var.get() == "csv":
            identifiers = read_csv(Path(csv_path_entry.get()), csv_column_entry.get())
        else:
            identifiers = parse(text_input.get("1.0", tk.END))

        idents, dup = deduplicate(identifiers)
        output = output_entry.get()
        folder = Path(output) if output else Path("output")
        folder.mkdir(parents=True, exist_ok=True)

        errors = 0
        for ident in idents:
            try:
                export(generate(ident), ident, folder)
            except Exception as e:
                errors += 1
                messagebox.showinfo("Error", f"Error: {e}")

        messagebox.showinfo(
            "Reporte",
            f"{len(identifiers)} identificadores recibidos\n"
            f"{len(idents)} QR generados\n"
            f"{dup} duplicados eliminados\n"
            f"{errors} errores"
        )

    #trace de la app
    source_var.trace_add("write", on_mode_change)
    on_mode_change()
    root.mainloop()