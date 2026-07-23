import csv

from pathlib import Path

def read_csv(path: Path, column: str) -> list[str]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        idents = []
        for row in reader:
            val = row.get(column)
            idents.append(val.strip())
    return idents