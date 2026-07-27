def parse(text: str) -> list[str]:
    results = []
    for lineas in text.split("\n"):
        for linea in lineas.split(","):
            if linea.strip():
                results.append(linea.strip())
    return results