from pathlib import Path

from qrgen.core.parser import parse
from qrgen.core.deduplicator import deduplicate
from qrgen.core.generator import generate
from qrgen.core.exporter import export
from qrgen.io.csv_reader import read_csv

def run() -> None:
    mode: str = input("Fuente de Entrada:\n  1. Manual\n  2. CSV\nElige (1/2): ")
    
    if mode == '1':
        text = input("Identificador: ")
        identifiers = parse(text)
    elif mode == '2':
        csv_archive = Path(input("Ruta del archivo CSV: "))
        idnt_column: str = input("Columna de identificadores: ")
        identifiers = read_csv(csv_archive, idnt_column)
    else:
        print("Opcion no valida")
        return
        
    idents, dup  = deduplicate(identifiers)
    input_path = input("Carpeta destino [output]: ").strip()
    folder = Path(input_path) if input_path else Path("output")
    folder.mkdir(parents=True, exist_ok=True)
    
    print(f"{idents}")
    
    errors:int = 0
    for ident in idents:
        try:
            export(generate(ident), ident, folder)
            
        except Exception as e:
            errors += 1
            print(f"Error: {e}")
        
    
    print(f"\n--Reporte--\n{len(identifiers)} identificadores recibidos\n{len(idents)} QR generados\n{dup} duplicados eliminados\n{errors} errores")