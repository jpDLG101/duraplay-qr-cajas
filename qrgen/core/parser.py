def parse(text: str) -> list[str]:
    result = []
    for lineas in text.split("\n"):
        for linea in lineas.split(","):
            result.append(linea.strip())
        
    return result