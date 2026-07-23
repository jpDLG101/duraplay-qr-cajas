from qrgen.core.parser import parse
from qrgen.core.deduplicator import deduplicate
from qrgen.core.generator import generate

def run() -> None:
    text = input("Identificador: ")
    identifiers = parse(text)
    ident, dup  = deduplicate(identifiers)
    if dup == 0:
        print(f"{ident}")
    else: 
        print(f"{ident}\n{dup} duplicados eliminados")
    
    generate(ident[0]).save("test.png")