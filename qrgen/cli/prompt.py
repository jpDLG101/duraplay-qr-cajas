from pathlib import Path

from qrgen.core.parser import parse
from qrgen.core.deduplicator import deduplicate
from qrgen.core.generator import generate
from qrgen.core.exporter import export

def run() -> None:
    text = input("Identificador: ")
    identifiers = parse(text)
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